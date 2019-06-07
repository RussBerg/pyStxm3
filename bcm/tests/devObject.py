


from bcm.devices import BaseObject




if __name__ == '__main__':
    def mycallback(kwargs):
        print(kwargs)


    app = QtWidgets.QApplication(sys.argv)
    obj = BaseObject('IOC:m912.RBV', write_pv='IOC:m913.VAL', val_only=True, val_kw='value')
    d = obj.add_device('IOC:m914.RBV', write_pv='IOC:m914.VAL', val_only=True, val_kw='timestamp')
    s = obj.add_device('SYSTEM:mode:fbk', val_only=True, val_kw='value')
    d.changed.connect(mycallback)
    s.changed.connect(mycallback)
    d.put(-6749.321)
    print('MODE fbk is: ', s.get())

    sys.exit(app.exec_())