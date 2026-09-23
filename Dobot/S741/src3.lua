-- This module is used to set up I/O, variables, etc. The motion command cannot be called here.
-- Version: Lua 5.3.5
local cleared = false
while true do
  Systime_correct()
  if current_time%86400 >= 28809 and current_time%86400 <= 28811 and not cleared then --tự động reset vào lúc 8h sáng hàng ngày
    OK = 0
    NG = 0
    total = 0
    cleared = true
  else cleared = false end
  Sleep(50)
end