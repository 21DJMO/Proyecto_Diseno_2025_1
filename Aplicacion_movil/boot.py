import bluetooth
from micropython import const
import time
import random
from ble_advertising import advertising_payload

# UUIDs del servicio UART (como el de Nordic)
_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_TX =  (bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"), bluetooth.FLAG_NOTIFY,)
_UART_RX =  (bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"), bluetooth.FLAG_WRITE,)
_UART_SERVICE = (_UART_UUID, (_UART_TX, _UART_RX,),)

class BLEUART:
    def __init__(self, ble, name="ESP32"):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)

        ((self._tx_handle, self._rx_handle),) = self._ble.gatts_register_services((_UART_SERVICE,))
        self._connections = set()
        self._payload = advertising_payload(name=name, services=[_UART_UUID])
        self._advertise()

    def _advertise(self):
        try:
            self._ble.gap_advertise(None)  # Detener publicidad anterior
            self._ble.gap_advertise(100_000, adv_data=self._payload)
            print("🔵 Publicidad BLE activa")
        except OSError as e:
            print("⚠️ Error al anunciar BLE:", e)

    def _irq(self, event, data):
        if event == 1:  # _IRQ_CENTRAL_CONNECT
            conn_handle, _, _ = data
            self._connections.add(conn_handle)
            print("🔗 Dispositivo conectado")
        elif event == 2:  # _IRQ_CENTRAL_DISCONNECT
            conn_handle, _, _ = data
            self._connections.remove(conn_handle)
            self._advertise()
            print("❌ Dispositivo desconectado")
        elif event == 3:  # _IRQ_GATTS_WRITE
            conn_handle, value_handle = data
            value = self._ble.gatts_read(self._rx_handle)
            mensaje = value.replace(b'\x00', b'').decode('utf-8', 'ignore').strip()
            print("📥 Recibido: ", mensaje)

    def send(self, data):
        for conn_handle in self._connections:
            self._ble.gatts_notify(conn_handle, self._tx_handle, data)

# Inicialización BLE
ble = bluetooth.BLE()
uart = BLEUART(ble)
min_val = 59.8
max_val = 60.1
unidad="mA"

while True:
    Corriente= random.uniform(min_val, max_val)
    CorrienteRMS= random.uniform(min_val, max_val)
    Mensaje=str(Corriente)+","+str(CorrienteRMS)+","+unidad+","
    uart.send(Mensaje+"\n")
    print("Enviado: ["+Mensaje+"]")
    time.sleep_ms(2000)
