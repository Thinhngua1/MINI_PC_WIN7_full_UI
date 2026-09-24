-- This module is used to set up I/O, variables, etc. The motion command cannot be called here.
-- Version: Lua 5.3.5
local ip = "192.168.10.5" --ip máy tính
local port = 8500
local shift = 0
local interval = 10 --thời gian gửi data, tính theo giây (s)
local NG = 0
local cleared = false

while true do
  ::create_server::
  local err, socket = TCPCreate(false, ip, port)
  if err ~= 0 then
    print("Failed to create socket, re-connecting")
    Sleep(1000)
    goto create_server
  end
  err = TCPStart(socket, 3)
  if err ~= 0 then
    print("Failed to connect server, re-connecting")
    TCPDestroy(socket)
    Sleep(1000)
    goto create_server
  end
  while true do
    local ack = {}
    Systime_correct()
    --while not((current_time%interval >= 0 and current_time%interval < 5) or DI(3) == 1 or runMode ~= '') do
    while not((current_time%interval >= 0 and current_time%interval < 5) or DI(3) == 1) do
      Sleep(50)
      Systime_correct()
    end
    print(os.date('%c',current_time))
    total = OK + NG
    rate = (total == 0) and 0 or OK / total
    local msg = string.format('%s,%s,%d,%d,%d,%.2f,%d,Change Tray,%s',name, model, total, OK, NG, rate*100, shift, runMode)
    TCPWrite(socket, msg)
    --[[
    ack = select(2, TCPRead(socket, 0, 'string'))
    print(ack)

    if ack then Sleep(5000)
    else
      print('Connection to server is interrupted, re-connecting.')
      TCPDestroy(socket)
      Sleep(1000)
      goto create_server
    end
    ]]--
    while DI(3) == 1 do Sleep(50) end
  end
end
