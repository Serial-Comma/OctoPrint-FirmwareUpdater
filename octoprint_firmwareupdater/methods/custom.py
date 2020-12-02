import os
import sarge

def _check_custom(self):
    custom_commandline = self._settings.get(["custom_commandline"])
    custom_workingdir = self._settings.get(["custom_workingdir"])

    return_value = True
    if custom_workingdir is not None and custom_workingdir != "":
        if not os.path.exists(custom_workingdir):
            self._logger.error(u"Custom command working directory does not exist: {path}".format(path=custom_workingdir))
            return_value = False

    return return_value

def _flash_custom(self, firmware=None, printer_port=None):
    assert(firmware is not None)
    assert(printer_port is not None)

    custom_commandline = self._settings.get(["custom_commandline"])
    custom_commandline = custom_commandline.replace("{firmware}", firmware)
    custom_commandline = custom_commandline.replace("{port}", printer_port)

    custom_workingdir = self._settings.get(["custom_workingdir"])
    if custom_workingdir is None or custom_workingdir == "":
        custom_workingdir = os.getcwd()

    self._logger.info(u"Running '{}' in {}".format(custom_commandline, custom_workingdir))
    self._console_logger.info(u"")
    self._console_logger.info(custom_commandline)
    try:
        p = sarge.run(custom_commandline, cwd=custom_workingdir, async_=True, stdout=sarge.Capture(), stderr=sarge.Capture())
        p.wait_events()

        while p.returncode is None:
            output = p.stdout.read(timeout=0.5).decode('utf-8')
            if not output:
                p.commands[0].poll()
                continue

            for line in output.split("\n"):
                if line.endswith("\r"):
                    line = line[:-1]
                self._console_logger.info(u"> {}".format(line))

            self._logger.info(u"Running custom command(s)...")
            self._send_status("progress", subtype="runningcustom")

            # if AVRDUDE_WRITING in output:
            #     self._logger.info(u"Writing memory...")
            #     self._send_status("progress", subtype="writing")
            # elif AVRDUDE_VERIFYING in output:
            #     self._logger.info(u"Verifying memory...")
            #     self._send_status("progress", subtype="verifying")
            # elif AVRDUDE_TIMEOUT in output:
            #     p.commands[0].kill()
            #     p.close()
            #     raise FlashException("Timeout communicating with programmer")
            # elif AVRDUDE_ERROR_DEVICE in output:
            #     p.commands[0].kill()
            #     p.close()
            #     raise FlashException("Error opening serial device")
            # elif AVRDUDE_ERROR_VERIFICATION in output:
            #     p.commands[0].kill()
            #     p.close()
            #     raise FlashException("Error verifying flash")
            # elif AVRDUDE_ERROR_SYNC in output:
            #     p.commands[0].kill()
            #     p.close()
            #     raise FlashException("Avrdude says: 'not in sync" + output[output.find(AVRDUDE_ERROR_SYNC) + len(AVRDUDE_ERROR_SYNC):].strip() + "'")
            # elif AVRDUDE_ERROR in output:
            #     raise FlashException("Avrdude error: " + output[output.find(AVRDUDE_ERROR) + len(AVRDUDE_ERROR):].strip())

        if p.returncode == 0:
            return True
        else:
            raise FlashException("Custom command returned code {returncode}".format(returncode=p.returncode))

    except FlashException as ex:
        self._logger.error(u"Flashing failed. {error}.".format(error=ex.reason))
        self._send_status("flasherror", message=ex.reason)
        return False
    except:
        self._logger.exception(u"Flashing failed. Unexpected error.")
        self._send_status("flasherror")
        return False

class FlashException(Exception):
	def __init__(self, reason, *args, **kwargs):
		Exception.__init__(self, *args, **kwargs)
		self.reason = reason