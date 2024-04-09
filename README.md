# TIC2mqtt #
A python script to read TIC data from the Linky meter and publish to mqtt. Also provides effective power in W.

This script reads a serial input and retrieves the TIC data if any. Only adapted to TEMPO contracts with EDF as a supplier.
To read the tic data, the reference documentation is from ENEDIS: Enedis-NOI-CPT_54E, 06/2018 https://www.enedis.fr/media/2035/download

Once data is recovered, the script updates a few mqqt topics. Computes Power based on energy consumption as a bonus.
Feel free to use this code as per the license file on github
All is in english here, but 99% of users mights be French so... Bonjour à vous !
Disclamer! This code is provided free of charge for you to use. However, errors, bugs or issues might araise.
Please, take your responsabilities. I cannot be held responsible for any loss that might be induced from the use of this script.

## Functionalities ##
- Init a port com to match Linky baud rate etc
- Reads important fields
- Check for malformed data
- Computes read effective power (W) based on the Wh meter.
- Adapatative time step to compute power:
-   High power loads will show up fast
-   Sudden drop in power will prevent actual power from being reported immediately but will settle after a few cycles.

-   Soufian YJJOU, 2024.
