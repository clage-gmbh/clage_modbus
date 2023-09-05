// CLAGE modbus client
//
#include <modbus.h>
#include <sys/select.h>  // using select()

#include <cstring>  // using strerror()
#include <iostream>

class clage_modbus {
   private:
    modbus_t* m_ctx;

   public:
    clage_modbus(const std::string& uart, unsigned baudrate, char parity, unsigned databits, unsigned stopbits) : m_ctx(nullptr) {
        m_ctx = modbus_new_rtu(uart.c_str(), baudrate, parity, databits, stopbits);
        if (nullptr == m_ctx) {
            std::cerr << "Failed to create modbus RTU client." << std::endl;
            std::exit(2);
        }
    }
    void connect(void) {
        if (-1 == modbus_connect(m_ctx)) {
            std::cerr << "Failed to connect modbus RTU client." << std::endl;
            std::exit(2);
        }
    }
    void disconnect(void) {
        modbus_close(m_ctx);
    }

    void set_response_timeout(struct timeval& tv) {
        modbus_set_response_timeout(m_ctx, tv.tv_sec, tv.tv_usec);
    }

    void set_server(uint8_t server_address) {
        modbus_set_slave(m_ctx, server_address);
    }

    bool is_connected(void) {
        int socket = modbus_get_socket(m_ctx);
        fd_set rfds;
        FD_ZERO(&rfds);
        FD_SET(socket, &rfds);
        struct timeval tv;
        tv.tv_sec = 1;
        tv.tv_usec = 0;
        int retval = select(socket + 1, &rfds, NULL, NULL, &tv);
        if (retval == -1) {
            std::cerr << "Error in select(): " << strerror(errno) << std::endl;
            return false;
        }
        else if (retval == 0) {
            return false;
        }
        else {
            return true;
        }
    }

    ~clage_modbus() {
        if (nullptr != m_ctx) {
            modbus_free(m_ctx);
        }
        m_ctx = nullptr;
    }
};

int main() {
    modbus_t* ctx;
    uint16_t reg[2];

    ctx = modbus_new_rtu("/dev/ttyUSB2", 19200, 'N', 8, 1);
    if (ctx == NULL) {
        std::cerr << "Failed to create Modbus context." << std::endl;
        return 1;
    }

    if (modbus_connect(ctx) == -1) {
        std::cerr << "Modbus connection failed: " << modbus_strerror(errno) << std::endl;
        modbus_free(ctx);
        return 1;
    }

    modbus_set_response_timeout(ctx, 2, 0);
    modbus_set_slave(ctx, 97);

    if (modbus_read_input_registers(ctx, 0, 2, reg) == -1) {
        std::cerr << "Failed to read input registers: " << modbus_strerror(errno) << std::endl;
        modbus_close(ctx);
        modbus_free(ctx);
        return 1;
    }

    std::cout << "R0=" << reg[0] << std::endl;
    std::cout << "R1=" << reg[1] << std::endl;

    modbus_close(ctx);
    modbus_free(ctx);

    return 0;
}

// EOF