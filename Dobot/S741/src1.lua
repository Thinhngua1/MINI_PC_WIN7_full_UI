-- This module is used to set up I/O, variables, etc. The motion command cannot be called here.
-- Version: Lua 5.3.5
local ip = "192.168.10.5" --ip máy tính
local port = 8500
local shift = 0
local interval = 10 --thời gian gửi data, tính theo giây (s)
local NG = 0
local cleared = false
-- khóa chu kỳ gửi data 1 lần / current_time%interval
local last_send_slot = -1


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
    local current_slot = current_time // interval
    local in_send_window = (current_time % interval) < 5

    while last_send_slot == current_slot or (not in_send_window and DI(3) ~= 1 and runMode == '') do
      Sleep(50)
      Systime_correct()

      current_slot = current_time // interval
      in_send_window = (current_time % interval) < 5
    end
    print(os.date('%c',current_time))
    total = OK + NG
    rate = (total == 0) and 0 or OK / total
    local msg = string.format('%s,%s,%d,%d,%d,%.2f,%d,Change Tray,%s',name, model, total, OK, NG, rate*100, shift, runMode)
    TCPWrite(socket, msg)
    -- ack = select(2, TCPRead(socket, 0, 'string'))
    -- print(ack)

    -- if ack then Sleep(5000)
    -- else
    --   print('Connection to server is interrupted, re-connecting.')
    --   TCPDestroy(socket)
    --   Sleep(1000)
    --   goto create_server
    -- end

      -- Khóa không cho gửi lại trong cùng chu kỳ
    last_send_slot = current_slot

    while DI(3) == 1 do Sleep(50) end
  end
end
