seconds = 0
timer = mp.add_periodic_timer(2, function()
	mp.command('sub-reload')
    seconds = seconds + 2
end)
