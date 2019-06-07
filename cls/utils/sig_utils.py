

from cls.utils.log import get_module_logger

_logger = get_module_logger(__name__)

def reconnect_signal(obj, sig, cb):
    '''
    This function takes the base object, the signal addr and the callback and checks first to see if the signal is still connected
    if it is it is disconnected before being connected to the callback
    ex:
        was:
            self.executingScan.sigs.changed.connect(self.add_line_to_plot)
        is:
            self.reconnect_signal(self.executingScan.sigs, self.executingScan.sigs.changed, self.add_line_to_plot)

    :param obj: base QObject
    :param sig: addr of signal instance
    :param cb: callback to attach signal to
    :return:


    '''
    if(obj.receivers(sig) > 0):
        #_logger.info('stxmMain: this sig is still connected, disconnnecting before reconnecting')
        sig.disconnect()

    # _logger.debug('stxmMain: connecting this signal')
    sig.connect(cb)


def disconnect_signal(obj, sig):
    '''
    This function takes the base object, the signal addr and checks first to see if the signal is still connected
    if it is it is disconnected

    :param obj: base QObject
    :param sig: addr of signal instance
    :return:


    '''
    if(obj.receivers(sig) > 0):
        #_logger.debug('stxmMain: this sig is still connected, disconnnecting')
        sig.disconnect()


