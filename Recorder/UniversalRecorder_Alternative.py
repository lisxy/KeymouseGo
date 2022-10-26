import re

import keyboard, mouse
from Event import ScreenWidth as SW, ScreenHeight as SH
import Recorder.globals as globalv

record_signals = globalv.RecordSignal()
from loguru import logger


def get_delay(message, current_time):
    current_time = int(current_time * 1e3)
    delay = current_time - globalv.latest_time

    # 录制鼠标轨迹的精度，数值越小越精准，但同时可能产生大量的冗余
    mouse_move_interval_ms = globalv.mouse_interval_ms or 999999

    if message == 'mouse move' and delay < mouse_move_interval_ms:
        return -1

    if globalv.latest_time < 0:
        delay = 0
    globalv.latest_time = current_time
    return delay


# def on_move(x, y):
#     event = get_mouse_event(x, y, )
#     if event:
#         record_signals.event_signal.emit(event)
#
#
# def on_click(x, y, button, pressed):
#     message = 'mouse {0} {1}'.format(button, 'down' if pressed else 'up')
#     event = get_mouse_event(x, y, message)
#     if event:
#         record_signals.event_signal.emit(event)


def on_mouse_event(event):
    if type(event) == mouse.ButtonEvent:
        event: mouse.ButtonEvent
        tpos = (-1, -1)
        message = f'mouse {event.button} ' \
                  f'{"down" if event.event_type == "double" else event.event_type}'
    elif type(event) == mouse.WheelEvent:
        event: mouse.WheelEvent
        message = 'mouse wheel {0}'.format('down' if event.delta < 0 else 'up')
        tpos = (-1, -1)
    elif type(event) == mouse.MoveEvent:
        event: mouse.MoveEvent
        tx = event.x / SW
        ty = event.y / SH
        tpos = (tx, ty)
        message = 'mouse move'
    delay = get_delay(message, event.time)
    if delay >= 0:
        record_signals.event_signal.emit(
            globalv.ScriptEvent({
                'delay': delay,
                'event_type': 'EM',
                'message': message,
                'action': tpos
            }
        ))


def get_keyboard_event(event: keyboard.KeyboardEvent, message):
    delay = get_delay(message, event.time)
    if delay < 0:
        return None
    else:
        keycode = event.scan_code
        keyname = event.name
        if keyname is None:
            return None
        if re.match('^([0-9])$', keyname) and keycode is None:
            keyname = 'num{}'.format(keyname)
        event = globalv.ScriptEvent({
            'delay': delay,
            'event_type': 'EK',
            'message': message,
            'action': (keycode, keyname, 0)
        })
        logger.debug(event)
        return event


def on_press(event: keyboard.KeyboardEvent):
    event = get_keyboard_event(event, 'key down')
    if event:
        record_signals.event_signal.emit(event)


def on_release(event: keyboard.KeyboardEvent):
    event = get_keyboard_event(event, 'key up')
    if event:
        record_signals.event_signal.emit(event)


def setuphook(commandline=False):
    if not commandline:
        mouse.hook(callback=on_mouse_event)
    keyboard.on_press(callback=on_press)
    keyboard.on_release(callback=on_release)
