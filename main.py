import modbus_tk
import modbus_tk.modbus_tcp as modbus_tcp
import modbus_tk.defines as mdef
import time

if __name__ == "__main__":

    logger = modbus_tk.utils.create_logger(name='console', record_format='%(message)s')
    logger.info("running...")

    server = modbus_tcp.TcpServer(port=502)
    server.start()

    slave1 = server.add_slave(1)
    # add 2 blocks of holding registers
    slave1.add_block('a', mdef.HOLDING_REGISTERS, 0, 100)  # address 0, length 100
    slave1.add_block('c', mdef.COILS, 0, 100)

    # set the values of registers at address 0
    slave1.set_values('a', 0, 0)
    slave1.set_values('c', 0, 1)

    run = True
    while run:
        time.sleep(2)
        value = slave1.get_values('a', 0, 1)
        value40001 = int(value[0])
        value = slave1.get_values('a', 1, 1)
        value40002 = int(value[0])

        print('40001:', value40001)
        print('40002:', value40002)
        # value40001 += 1
        # value40002 += 3
        # slave1.set_values('a', 0, value40001)
        # slave1.set_values('a', 1, value40002)