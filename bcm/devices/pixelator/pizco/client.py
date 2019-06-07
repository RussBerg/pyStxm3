import time

from pizco import Proxy

proxy = Proxy('tcp://127.0.0.1:8000')

print(('{} * {} = {}'.format(proxy.factor, 8, proxy.calculate(8))))

def on_factor_changed(new_value, old_value):
    print(('The factor was changed from {} to {}'.format(old_value, new_value)))
    print(('{} * {} = {}'.format(proxy.factor, 8, proxy.calculate(8))))

proxy.factor_changed.connect(on_factor_changed)

for n in (3, 4, 5):
    proxy.factor = n
    time.sleep(.5)