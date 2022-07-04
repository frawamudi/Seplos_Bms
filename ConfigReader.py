from configparser import ConfigParser

#Read config.ini file
config_object = ConfigParser()
config_object.read("config.ini")

#Get the password
userinfo = config_object["USERINFO"]
print("Password is {}".format(userinfo["password"]))

#Get the BMSPARAM
userinfo = config_object["BMSPARAM"]
print("Can_slaves {}".format(userinfo["mastercan"]))

#userinfo["mastercan"]