#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import os.path
import sys
import re
import signal
import hashlib
import re
import urllib2
from random import random
from time import sleep, time
from subprocess import Popen, PIPE, check_output
from threading import Thread
from Queue import Queue, Empty
import utils

from PySide import QtCore, QtGui


class AmountAdd(QtCore.QObject):
        sig = QtCore.Signal(int)


class AcceptorThread(QtCore.QThread):

    def __init__(self, parent=None):
        super(AcceptorThread, self).__init__(parent)
        self.exiting = False
        self.signal = AmountAdd()

    def run(self):
        self.billPath = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), 'acceptor.py')

        self.billProc = Popen(
            ['sudo', 'python', self.billPath],
            stdout=PIPE,
            close_fds=True,
            universal_newlines=True
        )
        self.billQueue = Queue()
        self.bill = Thread(target=self.enqueue_output,
                           args=(self.billProc.stdout, self.billQueue))
        self.bill.daemon = False
        self.bill.start()

        while not self.exiting:
            try:
                line = self.billQueue.get_nowait()
                amount = int(line)
                if amount:
                    self.signal.sig.emit(amount)
            except Empty:
                pass
            sleep(0.2)
        self.billProc.terminate()
        self.billProc.wait()

    def enqueue_output(self, out, queue):
        while True:
            line = out.readline()
            if line:
                queue.put(line.strip())
            else:
                break
        out.close()


class KeyPress(QtCore.QObject):
    sig = QtCore.Signal(unicode)


class NumPadButton(QtGui.QPushButton):

    def __init__(self, char, value, sig, *args, **kwargs):
        super(NumPadButton, self).__init__(*args, **kwargs)
        self.char = char
        self.value = value
        self.signal = sig
        self.init_ui()
        self.init_style()
        self.init_action()

    def init_ui(self):
        self.setText(self.char)

    def init_style(self):
        self.setStyleSheet('QPushButton {'
            'font-size: 15pt;'
            'background: #318AEF;'
            'color: #ffffff;}')

    def init_action(self):
        self.clicked.connect(self.on_click)

    def on_click(self):
        self.signal.sig.emit(self.value)


class NumPadWidget(QtGui.QWidget):

    def __init__(self, *args, **kwargs):
        super(NumPadWidget, self).__init__(*args, **kwargs)
        self.signal = KeyPress()
        self.init_ui()

    def init_ui(self):
        self._layout = QtGui.QGridLayout()
        self._layout.setHorizontalSpacing(10)
        self._layout.setVerticalSpacing(10)
        self.setLayout(self._layout)

        keys = [
            [['1', '1'], ['2', '2'], ['3', '3']],
            [['4', '4'], ['5', '5'], ['6', '6']],
            [['7', '7'], ['8', '8'], ['9', '9']],
            [['<', 'del'], ['0', '0'], ['', '']]
        ]

        for row, data in enumerate(keys):
            for col, el in enumerate(data):
                widget = NumPadButton(char=el[0], value=el[1],
                                      sig=self.signal)
                widget.setFocusPolicy(QtCore.Qt.NoFocus)
                self._layout.addWidget(widget, row, col, 1, 1)


class Manager(QtGui.QStackedWidget):

    def __init__(self, *args, **kwargs):
        super(Manager, self).__init__(*args, **kwargs)
        self.screen = dict()
        self.init_ui()
        self.init_style()
        self.parent().manager = self

    def init_ui(self):
        self.screen.update(
            start=StartPage(main=self.parent(), manager=self),
            phone=PhonePage(main=self.parent(), manager=self),
            pin=PinPage(main=self.parent(), manager=self),
            coin=CoinPage(main=self.parent(), manager=self),
            amount=AmountPage(main=self.parent(), manager=self),
            thank=ThankPage(main=self.parent(), manager=self),
        )
        for key, widget in self.screen.iteritems():
            self.addWidget(widget)

        self.change_widget('start')

    def change_widget(self, key):
        self.setCurrentWidget(self.screen[key])
        self.screen[key].on_show()

    def init_style(self):
        pass


class StartPage(QtGui.QWidget):

    def __init__(self, main, manager, *args, **kwargs):
        super(StartPage, self).__init__(*args, **kwargs)
        self.main = main
        self.manager = manager
        self.init_ui()
        self.init_style()
        self.init_action()

    def init_ui(self):
        self._layout = QtGui.QGridLayout()
        self.setLayout(self._layout)

        self.logo_label = QtGui.QLabel(parent=self)
        pixmap = QtGui.QPixmap('images/logo_start.ppm')
        self.logo_label.setPixmap(pixmap)
        self.logo_label.setMinimumWidth(pixmap.width())
        self.logo_label.setMinimumHeight(pixmap.height())

        self.description_label = QtGui.QLabel(parent=self)
        self.description_label.setText(u'''Каждый денежный переводзащищён современной
системой безопасности. Новейшие электронные
технологии и глобальная информационная сеть
позволяют выплачивать денежные средства
всего через несколько минут после их отправления.''')

        self.continue_label = QtGui.QLabel(parent=self)
        self.continue_label.setText(u'Для продолжения нажмите')

        self.continue_button = QtGui.QPushButton(parent=self)
        self.continue_button.setText(u'Ввод')
        self.continue_button.setFocusPolicy(QtCore.Qt.NoFocus)

        self._layout.addWidget(self.logo_label, 0, 0, 1, 4,
                               alignment=QtCore.Qt.AlignCenter)
        self._layout.addWidget(self.description_label, 1, 0, 1, 4,
                               alignment=QtCore.Qt.AlignCenter)
        self._layout.addWidget(self.continue_label, 2, 1, 1, 1)
        self._layout.addWidget(self.continue_button, 2, 2, 1, 1)

    def init_style(self):
        self.description_label.setStyleSheet('QLabel {'
            'font-size: 14pt;'
            'color: #000000;}')

        self.continue_label.setStyleSheet('QLabel {'
            'font-size: 15pt;'
            'color: #318AEF}')

        self.continue_button.setStyleSheet('QPushButton {'
            'font-size: 15pt;'
            'background: #318AEF;'
            'color: #ffffff;}')

    def init_action(self):
        self.continue_button.clicked.connect(self.on_continue)

    def on_show(self):
        pass

    def on_continue(self):
        self.manager.change_widget('phone')


class PhonePage(QtGui.QWidget):
    phone_format = '+7 ( %s%s%s ) %s%s%s - %s%s - %s%s'

    def __init__(self, main, manager, *args, **kwargs):
        super(PhonePage, self).__init__(*args, **kwargs)
        self.main = main
        self.manager = manager
        self.init_ui()
        self.init_style()
        self.init_action()

    def init_ui(self):
        self._layout = QtGui.QGridLayout()
        self.setLayout(self._layout)

        self.phone_label = QtGui.QLabel(parent=self)
        self.phone_label.setText('+7 ( ___ ) ___ - __ - __')
        self.phone_label.setAlignment(QtCore.Qt.AlignCenter)
        self.phone_label.setMinimumWidth(self.main.width())

        self.description_label = QtGui.QLabel(parent=self)
        self.description_label.setText(u'Введите номер своего телефона')

        self.numpad = NumPadWidget(parent=self)

        self.continue_label = QtGui.QLabel(parent=self)
        self.continue_label.setText(u'Для продолжения нажмите')

        self.continue_button = QtGui.QPushButton(parent=self)
        self.continue_button.setText(u'Ввод')
        self.continue_button.setFocusPolicy(QtCore.Qt.NoFocus)

        self._layout.addWidget(self.phone_label, 0, 0, 1, 4,
                               alignment=QtCore.Qt.AlignCenter)
        self._layout.addWidget(self.description_label, 1, 0, 1, 4,
                               alignment=QtCore.Qt.AlignCenter)
        self._layout.addWidget(self.numpad, 2, 1, 5, 2,
                               alignment=QtCore.Qt.AlignCenter)
        self._layout.addWidget(self.continue_label, 7, 1, 1, 1)
        self._layout.addWidget(self.continue_button, 7, 2, 1, 1)

    def init_style(self):
        self.phone_label.setStyleSheet('QLabel {'
            'font-size: 30pt;'
            'background: #d7eaff;'
            'color: #318AEF;'
            'font-weight: bold;'
            'padding: 15px 0px;}')

        self.description_label.setStyleSheet('QLabel {'
            'font-size: 14pt;'
            'color: #ff0000;}')

        self.continue_label.setStyleSheet('QLabel {'
            'font-size: 15pt;'
            'color: #318AEF}')

        self.continue_button.setStyleSheet('QPushButton {'
            'font-size: 15pt;'
            'background: #318AEF;'
            'color: #ffffff;}')

    def init_action(self):
        self.numpad.signal.sig.connect(self.on_keypress)
        self.continue_button.clicked.connect(self.on_continue)

    def on_show(self):
        self.phone_label.setText('+7 ( ___ ) ___ - __ - __')
        self.main.phone = ''
        self.main.pin = ''
        self.main.pin_count = 0

    def on_keypress(self, value):
        if value == 'del':
            self.main.phone = self.main.phone[:-1]
        elif len(self.main.phone) < 10:
            self.main.phone += value
        self.update_phone()

    def on_continue(self):
        if len(self.main.phone) != 10:
            return

        for i in range(10):
            data = 'phone=%s&timestamp=%i' % (
                self.main.phone, int(time()))
            signature = hashlib.sha256(
                (self.main.secret_key + data).encode('UTF-8')).hexdigest()

            try:
                resp = urllib2.urlopen(
                    self.main.check_url,
                    data=('key=%s&%s&signature=%s' % (
                        self.main.key, data, signature)).encode('UTF-8')
                )
                self.main.pin = resp.read().decode('utf-8').strip()

                if self.main.pin == '0':
                    self.manager.change_widget('start')
                elif self.main.pin == '1':
                    self.manager.change_widget('coin')
                else:
                    self.main.pin_count = 0
                    self.manager.change_widget('pin')

                return

            except urllib2.HTTPError as e:
                print 1, e
                break
            except urllib2.URLError as e:
                print 2
                continue
            except ValueError:
                print 3
                break

        self.manager.change_widget('start')

    def update_phone(self):
        phone = self.main.phone + '_' * (10 - len(self.main.phone))
        self.phone_label.setText(self.phone_format % tuple(d for d in phone))


class PinPage(QtGui.QWidget):
    pin_format = '%s %s %s %s'
    pin = ''

    def __init__(self, main, manager, *args, **kwargs):
        super(PinPage, self).__init__(*args, **kwargs)
        self.main = main
        self.manager = manager
        self.init_ui()
        self.init_style()
        self.init_action()

    def init_ui(self):
        self._layout = QtGui.QGridLayout()
        self.setLayout(self._layout)

        self.pin_label = QtGui.QLabel(parent=self)
        self.pin_label.setText('_ _ _ _')
        self.pin_label.setAlignment(QtCore.Qt.AlignCenter)
        self.pin_label.setMinimumWidth(self.main.width())

        self.description_label = QtGui.QLabel(parent=self)
        self.description_label.setText(u'''На указанный Вами номеротправлен
одноразовый четырёхзначный SMS-код.
Введите его для завершения регистрации.''')

        self.numpad = NumPadWidget(parent=self)

        self.continue_label = QtGui.QLabel(parent=self)
        self.continue_label.setText(u'Для продолжения нажмите')

        self.continue_button = QtGui.QPushButton(parent=self)
        self.continue_button.setText(u'Ввод')
        self.continue_button.setFocusPolicy(QtCore.Qt.NoFocus)

        self._layout.addWidget(self.pin_label, 0, 0, 1, 4,
                               alignment=QtCore.Qt.AlignCenter)
        self._layout.addWidget(self.description_label, 1, 0, 1, 4,
                               alignment=QtCore.Qt.AlignCenter)
        self._layout.addWidget(self.numpad, 2, 1, 5, 2,
                               alignment=QtCore.Qt.AlignCenter)
        self._layout.addWidget(self.continue_label, 7, 1, 1, 1)
        self._layout.addWidget(self.continue_button, 7, 2, 1, 1)

    def init_style(self):
        self.pin_label.setStyleSheet('QLabel {'
            'font-size: 30pt;'
            'background: #d7eaff;'
            'color: #318AEF;'
            'font-weight: bold;'
            'padding: 15px 0px;}')

        self.description_label.setStyleSheet('QLabel {'
            'font-size: 14pt;'
            'color: #ff0000;}')

        self.continue_label.setStyleSheet('QLabel {'
            'font-size: 15pt;'
            'color: #318AEF}')

        self.continue_button.setStyleSheet('QPushButton {'
            'font-size: 15pt;'
            'background: #318AEF;'
            'color: #ffffff;}')

    def init_action(self):
        self.numpad.signal.sig.connect(self.on_keypress)
        self.continue_button.clicked.connect(self.on_continue)

    def on_show(self):
        self.pin = ''
        self.pin_label.setText('_ _ _ _')
        self.description_label.setText(u'''На указанный Вами номеротправлен
одноразовый четырёхзначный SMS-код.
Введите его для завершения регистрации.''')

    def on_keypress(self, value):
        if value == 'del':
            self.pin = self.pin[:-1]
        elif len(self.pin) < 4:
            self.pin += value
        self.update_pin()

    def update_pin(self):
        pin = self.pin + '_' * (4 - len(self.pin))
        self.pin_label.setText(self.pin_format % tuple(d for d in pin))

    def on_continue(self):
        if len(self.pin) < 4:
            return

        self.main.pin_count += 1

        if self.main.pin == self.pin:
            self.confirm_user()
            self.manager.change_widget('coin')
            return

        if self.controller.pin_count < 3:
            self.pin = ''
            self.pin_label.setText('_ _ _ _')
            self.description_label.setText(
                u'\nКод введён неправильно. Повторите ввод.\n')
            return

        self.deny_user()
        self.controller.show_frame('start')

    def confirm_user(self):
        for i in range(10):
            data = 'phone=%s&timestamp=%i' % (
                self.main.phone, int(time()))
            signature = hashlib.sha256(
                (self.main.secret_key + data).encode('UTF-8')).hexdigest()
            try:
                resp = urllib2.urlopen(
                    self.main.confirm_url,
                    data=('key=%s&%s&signature=%s' % (
                        self.main.key, data, signature)).encode('UTF-8')
                )
                return
            except urllib2.HTTPError as e:
                break
            except urllib2.URLError:
                continue

    def deny_user(self):
        for i in range(10):
            data = 'phone=%s&timestamp=%i' % (
                self.main.phone, int(time()))
            signature = hashlib.sha256(
                (self.main.secret_key + data).encode('UTF-8')).hexdigest()
            try:
                resp = urllib2.urlopen(
                    self.main.deny_url,
                    data=('key=%s&%s&signature=%s' % (
                        self.main.key, data, signature)).encode('UTF-8')
                )
                return
            except urllib2.HTTPError as e:
                break
            except urllib2.URLError:
                continue


class CoinPage(QtGui.QWidget):

    def __init__(self, main, manager, *args, **kwargs):
        super(CoinPage, self).__init__(*args, **kwargs)
        self.main = main
        self.manager = manager
        self.init_ui()
        self.init_style()
        self.init_thread()
        self.init_action()
        self.init_timer()

    def init_ui(self):
        self._layout = QtGui.QGridLayout()
        self.setLayout(self._layout)

        self.logo_label = QtGui.QLabel(parent=self)
        pixmap = QtGui.QPixmap('images/logo.ppm')
        self.logo_label.setPixmap(pixmap)
        self.logo_label.setMinimumWidth(pixmap.width())
        self.logo_label.setMinimumHeight(pixmap.height())

        self.phone_label = QtGui.QLabel(parent=self)
        self.phone_label.setText(u'Ваш номер: ')

        self.amount_description_label = QtGui.QLabel(parent=self)
        self.amount_description_label.setText(u'Внесите деньги на счёт:')

        self.amount_label = QtGui.QLabel(parent=self)
        self.amount_label.setText(u'00 коп.')
        self.amount_label.setAlignment(QtCore.Qt.AlignCenter)
        self.amount_label.setMinimumWidth(self.main.width())

        self.continue_label = QtGui.QLabel(parent=self)
        self.continue_label.setText(u'Для продолжения нажмите')

        self.continue_button = QtGui.QPushButton(parent=self)
        self.continue_button.setText(u'Ввод')
        self.continue_button.setFocusPolicy(QtCore.Qt.NoFocus)

        self._layout.addWidget(self.logo_label, 0, 0, 2, 4,
                               alignment=QtCore.Qt.AlignCenter)
        self._layout.addWidget(self.phone_label, 2, 0, 1, 4,
                               alignment=QtCore.Qt.AlignCenter)
        self._layout.addWidget(self.amount_description_label, 3, 0, 1, 4,
                               alignment=QtCore.Qt.AlignCenter)
        self._layout.addWidget(self.amount_label, 4, 0, 2, 4,
                               alignment=QtCore.Qt.AlignCenter | QtCore.Qt.AlignTop)
        self._layout.addWidget(self.continue_label, 6, 1, 1, 1)
        self._layout.addWidget(self.continue_button, 6, 2, 1, 1)

    def init_style(self):
        self.phone_label.setStyleSheet('QLabel {'
            'font-size: 20pt;'
            'font-weight: bold;'
            'color: #ff0000;}')

        self.amount_description_label.setStyleSheet('QLabel {'
            'font-size: 18pt;'
            'font-weight: bold;'
            'color: #000000;}')

        self.amount_label.setStyleSheet('QLabel {'
            'font-size: 30pt;'
            'background: #d7eaff;'
            'color: #318AEF;'
            'font-weight: bold;'
            'padding: 15px 0px;}')

        self.continue_label.setStyleSheet('QLabel {'
            'font-size: 15pt;'
            'color: #318AEF}')

        self.continue_button.setStyleSheet('QPushButton {'
            'font-size: 15pt;'
            'background: #318AEF;'
            'color: #ffffff;}')

    def init_thread(self):
        self.acceptor = AcceptorThread(parent=self)

    def init_timer(self):
        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(False)
        self.timer.timeout.connect(self.on_continue)

    def init_action(self):
        self.continue_button.clicked.connect(self.on_continue)
        self.acceptor.signal.sig.connect(self.on_amount_add)

    def on_show(self):
        self.main.amount = 0
        self.phone_label.setText(
            u'Ваш номер: +7 (%s%s%s) %s%s%s-%s%s-%s%s' % tuple(
                d for d in self.main.phone))
        self.amount_label.setText(u'00 коп.')
        if self.acceptor.isRunning():
            self.acceptor.exiting = True
            self.acceptor.wait()
        self.acceptor.exiting = False
        self.acceptor.start()
        self.timer.start(30000)

    def on_continue(self):
        if self.acceptor.isRunning():
            self.acceptor.exiting = True
            self.acceptor.wait()
        for i in range(10):
            data = 'phone=%s&amount=%i&timestamp=%i' % (
                self.main.phone, self.main.amount, int(time()))
            signature = hashlib.sha256(
                (self.main.secret_key + data).encode('UTF-8')).hexdigest()
            try:
                resp = urllib2.urlopen(
                    self.main.refill_url,
                    data=('key=%s&%s&signature=%s' % (
                        self.main.key, data, signature)).encode('UTF-8')
                )
                break
            except urllib2.HTTPError as e:
                break
            except urllib2.URLError:
                continue
        self.timer.stop()
        self.manager.change_widget('amount')

    def on_amount_add(self, value):
        self.main.amount += value
        self.amount_label.setText(u'%02i коп.' % self.main.amount)
        self.timer.stop()
        self.timer.start(30000)


class AmountPage(QtGui.QWidget):

    def __init__(self, main, manager, *args, **kwargs):
        super(AmountPage, self).__init__(*args, **kwargs)
        self.main = main
        self.manager = manager
        self.init_ui()
        self.init_style()
        self.init_action()
        self.init_timer()

    def init_ui(self):
        self._layout = QtGui.QGridLayout()
        self.setLayout(self._layout)

        self.logo_label = QtGui.QLabel(parent=self)
        pixmap = QtGui.QPixmap('images/logo.ppm')
        self.logo_label.setPixmap(pixmap)
        self.logo_label.setMinimumWidth(pixmap.width())
        self.logo_label.setMinimumHeight(pixmap.height())

        self.phone_label = QtGui.QLabel(parent=self)
        self.phone_label.setText(u'Ваш номер: ')

        self.amount_description_label = QtGui.QLabel(parent=self)
        self.amount_description_label.setText(u'Вы внесли:')

        self.amount_label = QtGui.QLabel(parent=self)
        self.amount_label.setText(u'00 коп.')
        self.amount_label.setAlignment(QtCore.Qt.AlignCenter)
        self.amount_label.setMinimumWidth(self.main.width())

        self._layout.addWidget(self.logo_label, 0, 0, 2, 4,
                               alignment=QtCore.Qt.AlignCenter)
        self._layout.addWidget(self.phone_label, 2, 0, 1, 4,
                               alignment=QtCore.Qt.AlignCenter)
        self._layout.addWidget(self.amount_description_label, 3, 0, 1, 4,
                               alignment=QtCore.Qt.AlignCenter)
        self._layout.addWidget(self.amount_label, 4, 0, 2, 4,
                               alignment=QtCore.Qt.AlignCenter | QtCore.Qt.AlignTop)

    def init_style(self):
        self.phone_label.setStyleSheet('QLabel {'
            'font-size: 20pt;'
            'font-weight: bold;'
            'color: #ff0000;}')

        self.amount_description_label.setStyleSheet('QLabel {'
            'font-size: 18pt;'
            'font-weight: bold;'
            'color: #000000;}')

        self.amount_label.setStyleSheet('QLabel {'
            'font-size: 30pt;'
            'background: #d7eaff;'
            'color: #318AEF;'
            'font-weight: bold;'
            'padding: 15px 0px;}')

    def init_action(self):
        pass

    def init_timer(self):
        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(False)
        self.timer.timeout.connect(self.on_timer)

    def on_show(self):
        self.phone_label.setText(
            u'Ваш номер: +7 (%s%s%s) %s%s%s-%s%s-%s%s' % tuple(
                d for d in self.main.phone))
        self.amount_label.setText(u'%02i коп.' % self.main.amount)
        self.timer.start(5000)

    def on_timer(self):
        self.timer.stop()
        self.manager.change_widget('thank')


class ThankPage(QtGui.QWidget):

    def __init__(self, main, manager, *args, **kwargs):
        super(ThankPage, self).__init__(*args, **kwargs)
        self.main = main
        self.manager = manager
        self.init_ui()
        self.init_style()
        self.init_action()
        self.init_timer()

    def init_ui(self):
        self._layout = QtGui.QGridLayout()
        self.setLayout(self._layout)

        self.logo_label = QtGui.QLabel(parent=self)
        pixmap = QtGui.QPixmap('images/logo.ppm')
        self.logo_label.setPixmap(pixmap)
        self.logo_label.setMinimumWidth(pixmap.width())
        self.logo_label.setMinimumHeight(pixmap.height())

        self.thank_label = QtGui.QLabel(parent=self)
        self.thank_label.setText(u'Спасибо')

        self.description_label = QtGui.QLabel(parent=self)
        self.description_label.setText(u'''Каждый денежный переводзащищён современной
системой безопасности. Новейшие электронные
технологии и глобальная информационная сеть
позволяют выплачивать денежные средства
всего через несколько минут после их отправления.
''')

        self._layout.addWidget(self.logo_label, 0, 0, 2, 4,
                               alignment=QtCore.Qt.AlignCenter)
        self._layout.addWidget(self.thank_label, 2, 0, 1, 4,
                               alignment=QtCore.Qt.AlignCenter)
        self._layout.addWidget(self.description_label, 3, 0, 1, 4,
                               alignment=QtCore.Qt.AlignCenter)

    def init_style(self):

        self.thank_label.setStyleSheet('QLabel {'
            'font-size: 30pt;'
            'font-weight: bold;'
            'color: #318AEF;}')

        self.description_label.setStyleSheet('QLabel {'
            'font-size: 14pt;'
            'color: #000000;}')

    def init_timer(self):
        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(False)
        self.timer.timeout.connect(self.on_timer)

    def on_show(self):
        self.timer.start(5000)

    def init_action(self):
        pass

    def on_timer(self):
        self.timer.stop()
        self.manager.change_widget('start')


class Main(QtGui.QWidget):

    def __init__(self, *args, **kwargs):
        super(Main, self).__init__(*args, **kwargs)
        self.load_ini()
        self.init_ui()
        self.init_style()

    def load_ini(self):
        self.ini = utils.load_config()
        self.phone = ''
        self.amount = 0
        self.pin = ''
        self.pin_count = 0
        self.key = self.ini.get('main', 'key')
        self.secret_key = self.ini.get('main', 'secret_key')
        self.timeout = self.ini.getint('main', 'timeout')

        self.check_url = self.ini.get('main', 'check')
        self.confirm_url = self.ini.get('main', 'confirm')
        self.deny_url = self.ini.get('main', 'deny')
        self.refill_url = self.ini.get('main', 'refill')

    def init_ui(self):
        self.desktop = QtGui.QApplication.desktop()
        self._layout = QtGui.QGridLayout()
        self.setLayout(self._layout)

        self.manager = Manager(parent=self)
        self._layout.addWidget(self.manager, 0, 0)

        self.setWindowTitle('Money Box')
        rect = self.desktop.availableGeometry()
        #self.setGeometry(0, 0, self.desktop.width(), self.desktop.height())
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setGeometry(0, 0, 802, 480)
        self.show()

    def init_style(self):
        self.setStyleSheet('QWidget {'
            'background: #ffffff;}')

    def closeEvent(self, event):
        acceptor = self.manager.screen['coin'].acceptor
        if acceptor.isRunning():
            acceptor.exiting = True
            acceptor.wait()
            acceptor.terminate()
        event.accept()


def main():
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName('Music Box')
    ex = Main()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
