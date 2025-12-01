
import logging
from pyModbusTCP.client import ModbusClient

logging.basicConfig()
logging.getLogger('pyModbusTCP.client').setLevel(logging.DEBUG)


# --- 配置参数 ---
SERVER_HOST = "192.168.5.42"  # 服务器 IP 地址 (请修改为你设备的 IP)
SERVER_PORT = 502              # Modbus TCP 默认端口
# UNIT_ID = 1                    # 从站 ID (通常为 1，经过网关时很重要)

# 1. 实例化客户端
# auto_open=True 会在每次读写时自动尝试连接，非常方便
# auto_close=True 会在每次操作后自动关闭连接（适合低频通讯）
client = ModbusClient(host=SERVER_HOST, port=SERVER_PORT, auto_open=True)

print(f"尝试连接到 {SERVER_HOST}:{SERVER_PORT}...")

# client.read_coils(0)

# 2. 写入数据 (Write)
# 示例：向地址 100 写入单个寄存器值 123
write_addr = 50
write_value = 122

# write_single_register 返回 True 表示成功，False 表示失败
if client.write_single_register(write_addr, write_value):
    print(f"写入成功: 地址 {write_addr} -> 值 {write_value}")
else:
    print(f"写入失败: {client.last_error_as_txt}")

# 3. 读取数据 (Read)
# 示例：从地址 100 开始读取 2 个保持寄存器 (Holding Registers)
read_addr = 40
read_count = 122

# read_holding_registers 成功返回 list，失败返回 None
regs = client.read_holding_registers(read_addr, read_count)

if regs:
    print(f"读取成功: 地址 {read_addr} 开始的 {read_count} 个寄存器: {regs}")
else:
    print(f"读取失败: {client.last_error_as_txt}")

# 4. 操作线圈 (Coils - 布尔值)
# 示例：读取地址 0 的线圈状态
# coils = client.read_coils(0, 1)
# if coils:
#     print(f"线圈 0 状态: {coils}")
# else:
#     print("读取线圈失败")

# 5. 关闭连接 (如果未启用 auto_close，建议脚本结束时手动关闭)
client.close()