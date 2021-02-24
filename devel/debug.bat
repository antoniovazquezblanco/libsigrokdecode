REM set SIGROKDECODE_DIR=C:\Users\Anton\Projects\Github\libsigrokdecode\decoders\microchip_ezbl

sigrok-cli -i ezbl_full.sr -P uart,microchip_ezbl -A microchip_ezbl

pause