-- This module is used to set up I/O, variables, etc. The motion command cannot be called here.
-- Version: Lua 5.3.5
local ip = "192.168.10.5" --ip máy tính
local port = 8500
local shift = 0
local interval = 300 --thời gian gửi data, tính theo giây (s)
local NG = 0
local cleared = false

local last_periodic_time = 0
local previous_di3 = 0


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
    local di3_pressed = (DI(3) == 1 and previous_di3 == 0)
    local periodic_due = (current_time - last_periodic_time >= interval)

    if periodic_due or di3_pressed then

      print(os.date('%c',current_time))
      total = OK + NG
      rate = (total == 0) and 0 or OK / total
      local msg = string.format('%s,%s,%d,%d,%d,%.2f,%d,Change Tray,%s',name, model, total, OK, NG, rate*100, shift, runMode)
    
      local err = TCPWrite(socket, msg)
    -- confirm TCPwrite
    if err ~= 0 then
      print('TCPWrite failed, reconnecting')
      TCPDestroy(socket)
      Sleep(1000)
      goto create_server
    end
    -- ack = select(2, TCPRead(socket, 0, 'string'))
    -- print(ack)

    -- if ack then Sleep(5000)
    -- else
    --   print('Connection to server is interrupted, re-connecting.')
    --   TCPDestroy(socket)
    --   Sleep(1000)
    --   goto create_server
    -- end

    -- update khi gửi thành công 1  lần
    if periodic_due then 
      last_periodic_time = current_time
    end 
    previous_di3 = DI(3)  
  end
end
end