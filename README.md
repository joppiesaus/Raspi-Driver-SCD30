# SCD30

Software to read out SCD30 values on Raspberry Pi


## Prerequsites 

### Python 

Install the following python-libraries:

```
aptitude install python-crcmod
```

### Pigpiod

As the SCD30 needs complex i2c-commands, the Linux standard i2c-dev doesn't work. A working alternative is pigpiod.

```
aptitude install pigpio python-pigpio
```

Atm, IPv6 doesn't work on Raspbian correctly with pigpiod, so:

```
sed -i "s|^ExecStart=.*|ExecStart=/usr/bin/pigpiod -l -n 127.0.0.1|" /lib/systemd/system/pigpiod.service
systemctl restart pigpiod
# Test (should return an int)
pigs hwver
```

## I2C Clock stretching

Master needs to support Clock Stretching up to 150ms. The default in Raspbian is too low, we have to increase it:

To set it, download from here:

```
https://github.com/raspihats/raspihats/tree/master/clk_stretch
```

Compile:
```
gcc -o i2c1_set_clkt_tout i2c1_set_clkt_tout.c
gcc -o i2c1_get_clkt_tout i2c1_get_clkt_tout.c
```

execute (add to /etc/rc.local to run on every boot):

```
./i2c1_set_clkt_tout 20000 for 200ms
```

Remember: Maximum I2C speed for SCD30 is 100kHz.


