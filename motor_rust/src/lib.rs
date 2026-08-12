//! Captura de audio de baja latencia y detección de tono (algoritmo YIN) para AfinadorAccesible.
//!
//! Este módulo asume la parte sensible a precisión y latencia (acceso al dispositivo
//! de audio y estimación de frecuencia fundamental). La conversión a nota musical, la
//! lógica de instrucciones de afinación, la interfaz gráfica y la salida a NVDA se
//! quedan en Python, en `app/motor_audio.py`, `app/conector_nvda.py` e `app/interfaz_gui.py`.

use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::mpsc::{sync_channel, RecvTimeoutError};
use std::sync::Arc;
use std::thread::{self, JoinHandle};
use std::time::Duration;

use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use cpal::{Sample, SampleFormat};
use pyo3::exceptions::PyRuntimeError;
use pyo3::prelude::*;

const DURACION_VENTANA_SEGUNDOS: f32 = 0.1;

fn calcular_rms(muestras: &[f32]) -> f32 {
    if muestras.is_empty() {
        return 0.0;
    }
    let suma_cuadrados: f32 = muestras.iter().map(|&m| m * m).sum();
    (suma_cuadrados / muestras.len() as f32).sqrt()
}

/// Estima la frecuencia fundamental de una señal mono mediante el algoritmo YIN.
fn estimar_frecuencia_yin(senal: &[f32], tasa_muestreo: f32, umbral: f32, f_min: f32, f_max: f32) -> Option<f32> {
    let tamano = senal.len();
    let retardo_maximo = ((tasa_muestreo / f_min) as usize).min(tamano / 2);
    let retardo_minimo = ((tasa_muestreo / f_max) as usize).max(1);
    if retardo_maximo <= retardo_minimo || retardo_maximo == 0 {
        return None;
    }

    let longitud_segmento = tamano - retardo_maximo;
    let mut diferencia = vec![0.0f32; retardo_maximo];
    for retardo in 0..retardo_maximo {
        let mut suma = 0.0f32;
        for i in 0..longitud_segmento {
            let delta = senal[i] - senal[i + retardo];
            suma += delta * delta;
        }
        diferencia[retardo] = suma;
    }

    let mut diferencia_acumulada = vec![1.0f32; retardo_maximo];
    let mut suma_corrida = 0.0f32;
    for retardo in 1..retardo_maximo {
        suma_corrida += diferencia[retardo];
        diferencia_acumulada[retardo] = if suma_corrida > 0.0 {
            diferencia[retardo] * retardo as f32 / suma_corrida
        } else {
            1.0
        };
    }

    let mut retardo_elegido: Option<usize> = None;
    let mut retardo = retardo_minimo;
    while retardo < retardo_maximo {
        if diferencia_acumulada[retardo] < umbral {
            while retardo + 1 < retardo_maximo && diferencia_acumulada[retardo + 1] < diferencia_acumulada[retardo] {
                retardo += 1;
            }
            retardo_elegido = Some(retardo);
            break;
        }
        retardo += 1;
    }

    let retardo_elegido = retardo_elegido?;

    let retardo_final = if retardo_elegido > 0 && retardo_elegido < retardo_maximo - 1 {
        let anterior = diferencia_acumulada[retardo_elegido - 1];
        let actual = diferencia_acumulada[retardo_elegido];
        let siguiente = diferencia_acumulada[retardo_elegido + 1];
        let denominador = anterior - 2.0 * actual + siguiente;
        let ajuste = if denominador != 0.0 { (anterior - siguiente) / (2.0 * denominador) } else { 0.0 };
        retardo_elegido as f32 + ajuste
    } else {
        retardo_elegido as f32
    };

    if retardo_final <= 0.0 {
        return None;
    }
    Some(tasa_muestreo / retardo_final)
}

/// Dispositivo de entrada de audio disponible, expuesto a Python como tupla.
#[pyfunction]
fn listar_dispositivos_entrada(py: Python<'_>) -> PyResult<Vec<PyObject>> {
    let host = cpal::default_host();
    let dispositivos = host
        .input_devices()
        .map_err(|error| PyRuntimeError::new_err(format!("no se pudieron enumerar los dispositivos: {error}")))?;

    let mut resultado = Vec::new();
    for (indice, dispositivo) in dispositivos.enumerate() {
        let nombre = dispositivo.name().unwrap_or_else(|_| "Dispositivo desconocido".to_string());
        let tasa_muestreo = dispositivo
            .default_input_config()
            .map(|config| config.sample_rate().0)
            .unwrap_or(44100);
        let tupla = (indice, nombre, tasa_muestreo).into_py(py);
        resultado.push(tupla);
    }
    Ok(resultado)
}

enum ComandoCaptura {
    Detener,
}

/// Captura audio en dos hilos nativos (audio y análisis) y notifica cada bloque a Python.
///
/// El hilo de audio solo copia muestras a un canal acotado, sin bloquear en la GIL.
/// El hilo de análisis aplica la puerta de ruido y el algoritmo YIN, y entonces sí
/// adquiere la GIL para invocar el callback de Python con (frecuencia_o_none, rms).
#[pyclass]
struct CapturadorYinRust {
    indice_dispositivo: Option<usize>,
    umbral_yin: f32,
    umbral_rms: f32,
    tasa_muestreo_deseada: Option<u32>,
    duracion_ventana: f32,
    callback: Py<PyAny>,
    pausado: Arc<AtomicBool>,
    detener_analisis: Arc<AtomicBool>,
    control_audio: Option<std::sync::mpsc::Sender<ComandoCaptura>>,
    hilo_audio: Option<JoinHandle<()>>,
    hilo_analisis: Option<JoinHandle<()>>,
}

/// Busca entre las configuraciones soportadas por el dispositivo una que cubra la tasa de
/// muestreo pedida; si no se pide ninguna en concreto o no hay ninguna que la cubra, usa la
/// configuración por defecto del dispositivo.
fn resolver_config_entrada(
    dispositivo: &cpal::Device,
    tasa_muestreo_deseada: Option<u32>,
) -> Result<cpal::SupportedStreamConfig, String> {
    if let Some(tasa) = tasa_muestreo_deseada {
        let candidata = dispositivo
            .supported_input_configs()
            .map_err(|error| error.to_string())?
            .find(|rango| rango.min_sample_rate().0 <= tasa && tasa <= rango.max_sample_rate().0);
        if let Some(rango) = candidata {
            return Ok(rango.with_sample_rate(cpal::SampleRate(tasa)));
        }
    }
    dispositivo.default_input_config().map_err(|error| error.to_string())
}

#[pymethods]
impl CapturadorYinRust {
    #[new]
    #[pyo3(signature = (callback, indice_dispositivo=None, umbral_yin=0.15, umbral_rms=0.02, tasa_muestreo_deseada=None, duracion_ventana=DURACION_VENTANA_SEGUNDOS))]
    fn nuevo(
        callback: Py<PyAny>,
        indice_dispositivo: Option<usize>,
        umbral_yin: f32,
        umbral_rms: f32,
        tasa_muestreo_deseada: Option<u32>,
        duracion_ventana: f32,
    ) -> Self {
        CapturadorYinRust {
            indice_dispositivo,
            umbral_yin,
            umbral_rms,
            tasa_muestreo_deseada,
            duracion_ventana,
            callback,
            pausado: Arc::new(AtomicBool::new(false)),
            detener_analisis: Arc::new(AtomicBool::new(false)),
            control_audio: None,
            hilo_audio: None,
            hilo_analisis: None,
        }
    }

    fn iniciar(&mut self) -> PyResult<()> {
        if self.hilo_audio.is_some() {
            return Ok(());
        }

        let host = cpal::default_host();
        let dispositivo = match self.indice_dispositivo {
            Some(indice) => host
                .input_devices()
                .map_err(|error| PyRuntimeError::new_err(error.to_string()))?
                .nth(indice)
                .ok_or_else(|| PyRuntimeError::new_err("dispositivo de entrada no encontrado"))?,
            None => host
                .default_input_device()
                .ok_or_else(|| PyRuntimeError::new_err("no hay dispositivo de entrada por defecto"))?,
        };

        let config = resolver_config_entrada(&dispositivo, self.tasa_muestreo_deseada)
            .map_err(|error| PyRuntimeError::new_err(format!("no se pudo leer la configuración del dispositivo: {error}")))?;

        let tasa_muestreo = config.sample_rate().0 as f32;
        let canales = config.channels() as usize;
        let formato_muestra = config.sample_format();
        let tamano_ventana = ((tasa_muestreo * self.duracion_ventana) as usize).max(1024);

        let (tx_muestras, rx_muestras) = sync_channel::<Vec<f32>>(4);
        let (tx_control, rx_control) = std::sync::mpsc::channel::<ComandoCaptura>();
        let (tx_arranque, rx_arranque) = std::sync::mpsc::channel::<Result<(), String>>();
        let pausado_audio = Arc::clone(&self.pausado);

        let stream_config: cpal::StreamConfig = config.into();
        let err_fn = |error| eprintln!("error en el flujo de entrada de audio: {error}");

        let hilo_audio = thread::spawn(move || {
            let resultado_flujo = match formato_muestra {
                SampleFormat::F32 => dispositivo.build_input_stream(
                    &stream_config,
                    move |datos: &[f32], _| {
                        if pausado_audio.load(Ordering::Relaxed) {
                            return;
                        }
                        // Se promedian todos los canales en vez de tomar solo el primero:
                        // algunos dispositivos compuestos (arrays de varios micrófonos con
                        // procesamiento propio de Windows) reparten la señal útil entre
                        // canales, y quedarse solo con el canal 0 puede dejar la captura
                        // prácticamente muda aunque el dispositivo funcione bien en otras
                        // aplicaciones.
                        let mono: Vec<f32> = datos
                            .chunks(canales)
                            .map(|marco| marco.iter().sum::<f32>() / marco.len() as f32)
                            .collect();
                        let _ = tx_muestras.try_send(mono);
                    },
                    err_fn,
                    None,
                ),
                SampleFormat::I16 => dispositivo.build_input_stream(
                    &stream_config,
                    move |datos: &[i16], _| {
                        if pausado_audio.load(Ordering::Relaxed) {
                            return;
                        }
                        let mono: Vec<f32> = datos
                            .chunks(canales)
                            .map(|marco| marco.iter().map(|m| m.to_float_sample()).sum::<f32>() / marco.len() as f32)
                            .collect();
                        let _ = tx_muestras.try_send(mono);
                    },
                    err_fn,
                    None,
                ),
                SampleFormat::U16 => dispositivo.build_input_stream(
                    &stream_config,
                    move |datos: &[u16], _| {
                        if pausado_audio.load(Ordering::Relaxed) {
                            return;
                        }
                        let mono: Vec<f32> = datos
                            .chunks(canales)
                            .map(|marco| marco.iter().map(|m| m.to_float_sample()).sum::<f32>() / marco.len() as f32)
                            .collect();
                        let _ = tx_muestras.try_send(mono);
                    },
                    err_fn,
                    None,
                ),
                SampleFormat::I32 => dispositivo.build_input_stream(
                    &stream_config,
                    move |datos: &[i32], _| {
                        if pausado_audio.load(Ordering::Relaxed) {
                            return;
                        }
                        let mono: Vec<f32> = datos
                            .chunks(canales)
                            .map(|marco| marco.iter().map(|m| m.to_float_sample()).sum::<f32>() / marco.len() as f32)
                            .collect();
                        let _ = tx_muestras.try_send(mono);
                    },
                    err_fn,
                    None,
                ),
                SampleFormat::U32 => dispositivo.build_input_stream(
                    &stream_config,
                    move |datos: &[u32], _| {
                        if pausado_audio.load(Ordering::Relaxed) {
                            return;
                        }
                        let mono: Vec<f32> = datos
                            .chunks(canales)
                            .map(|marco| marco.iter().map(|m| m.to_float_sample()).sum::<f32>() / marco.len() as f32)
                            .collect();
                        let _ = tx_muestras.try_send(mono);
                    },
                    err_fn,
                    None,
                ),
                otro => {
                    let mensaje = format!("formato de muestra del dispositivo no soportado: {otro:?}");
                    eprintln!("{mensaje}");
                    let _ = tx_arranque.send(Err(mensaje));
                    return;
                }
            };

            let flujo = match resultado_flujo {
                Ok(flujo) => flujo,
                Err(error) => {
                    let mensaje = format!("no se pudo construir el flujo de entrada: {error}");
                    eprintln!("{mensaje}");
                    let _ = tx_arranque.send(Err(mensaje));
                    return;
                }
            };

            if let Err(error) = flujo.play() {
                let mensaje = format!("no se pudo iniciar el flujo de entrada: {error}");
                eprintln!("{mensaje}");
                let _ = tx_arranque.send(Err(mensaje));
                return;
            }

            let _ = tx_arranque.send(Ok(()));

            // El flujo debe permanecer vivo en este hilo hasta recibir la orden de detener.
            let _ = rx_control.recv();
            drop(flujo);
        });

        match rx_arranque.recv_timeout(Duration::from_secs(5)) {
            Ok(Ok(())) => {}
            Ok(Err(mensaje)) => {
                let _ = hilo_audio.join();
                return Err(PyRuntimeError::new_err(mensaje));
            }
            Err(_) => {
                return Err(PyRuntimeError::new_err(
                    "el hilo de captura de audio no confirmó su arranque a tiempo",
                ));
            }
        }

        let callback = Python::with_gil(|py| self.callback.clone_ref(py));
        let umbral_yin = self.umbral_yin;
        let umbral_rms = self.umbral_rms;
        let detener_analisis = Arc::clone(&self.detener_analisis);
        detener_analisis.store(false, Ordering::Relaxed);

        let hilo_analisis = thread::spawn(move || {
            let mut ventana: Vec<f32> = Vec::with_capacity(tamano_ventana * 2);
            loop {
                if detener_analisis.load(Ordering::Relaxed) {
                    break;
                }
                match rx_muestras.recv_timeout(Duration::from_millis(200)) {
                    Ok(bloque) => {
                        ventana.extend_from_slice(&bloque);
                        if ventana.len() >= tamano_ventana {
                            let inicio = ventana.len() - tamano_ventana;
                            let rms = calcular_rms(&ventana[inicio..]);
                            let frecuencia = if rms >= umbral_rms {
                                estimar_frecuencia_yin(&ventana[inicio..], tasa_muestreo, umbral_yin, 60.0, 1500.0)
                            } else {
                                None
                            };
                            ventana.clear();

                            Python::with_gil(|py| {
                                let argumento_frecuencia = match frecuencia {
                                    Some(valor) => valor.into_py(py),
                                    None => py.None(),
                                };
                                if let Err(error) = callback.call1(py, (argumento_frecuencia, rms)) {
                                    PyErr::print(&error, py);
                                }
                            });
                        }
                    }
                    Err(RecvTimeoutError::Timeout) => continue,
                    Err(RecvTimeoutError::Disconnected) => break,
                }
            }
        });

        self.control_audio = Some(tx_control);
        self.hilo_audio = Some(hilo_audio);
        self.hilo_analisis = Some(hilo_analisis);
        Ok(())
    }

    fn detener(&mut self) {
        self.detener_analisis.store(true, Ordering::Relaxed);
        if let Some(control) = self.control_audio.take() {
            let _ = control.send(ComandoCaptura::Detener);
        }
        if let Some(hilo) = self.hilo_audio.take() {
            let _ = hilo.join();
        }
        if let Some(hilo) = self.hilo_analisis.take() {
            let _ = hilo.join();
        }
    }

    fn pausar(&self) {
        self.pausado.store(true, Ordering::Relaxed);
    }

    fn reanudar(&self) {
        self.pausado.store(false, Ordering::Relaxed);
    }
}

#[pymodule]
fn motor_rust(_py: Python<'_>, modulo: &Bound<'_, PyModule>) -> PyResult<()> {
    modulo.add_function(wrap_pyfunction!(listar_dispositivos_entrada, modulo)?)?;
    modulo.add_class::<CapturadorYinRust>()?;
    Ok(())
}
