import datetime
import os
import time
import time_english
import time_german
import time_swabian
import time_dutch
import time_bavarian
import time_swiss_german
import time_swiss_german2
import wordclock_tools.wordclock_colors as wcc

class plugin:
    '''
    A class to display the current time (default mode).
    This default mode needs to be adapted to the hardware
    layout of the wordclock (the choosen stencil) and is
    the most essential time display mode of the wordclock.
    '''

    def __init__(self, config):
        '''
        Initializations for the startup of the current wordclock plugin
        '''
        # Get plugin name (according to the folder, it is contained in)
        self.name = os.path.dirname(__file__).split('/')[-1]

        # Choose language
        language = config.get('plugin_' + self.name, 'language')
        print('choosen language is ' + language)
        if language == 'dutch':
            self.taw = time_dutch.time_dutch()
        elif language == 'english':
            self.taw = time_english.time_english()
        elif language == 'german':
            self.taw = time_german.time_german()
        elif language == 'swabian':
            self.taw = time_swabian.time_swabian()
        elif language == 'bavarian':
            self.taw = time_bavarian.time_bavarian()
        elif language == 'swiss_german':
            self.taw = time_swiss_german.time_swiss_german()
        elif language == 'swiss_german2':
            self.taw = time_swiss_german2.time_swiss_german2()
        else:
            print('Could not detect language: ' + language + '.')
            print('Choosing default: german')
            self.taw = time_german.time_german()

        try:
            self.typewriter = config.getboolean('plugin_' + self.name, 'typewriter')
        except:
            print('  No typewriter-flag set for default plugin within the config-file. Typewriter animation will be used.')
            self.typewriter = True

        try:
            self.typewriter_speed = config.getint('plugin_' + self.name, 'typewriter_speed')
        except:
            self.typewriter_speed = 5
            print('  No typewriter_speed set for default plugin within the config-file. Defaulting to ' + str(self.typewriter_speed) + '.')

        self.bg_color     = wcc.BLACK  # default background color
        self.word_color   = wcc.WWHITE # default word color
        self.minute_color = wcc.WWHITE # default minute color

        # Other color modes...
        self.color_modes = \
               [[wcc.BLACK, wcc.WWHITE, wcc.WWHITE],
                [wcc.BLACK, wcc.WHITE, wcc.WHITE],
                [wcc.BLACK, wcc.ORANGE, wcc.ORANGE],
                [wcc.BLACK, wcc.ORANGE, wcc.WWHITE],
                [wcc.BLACK, wcc.PINK, wcc.GREEN],
                [wcc.BLACK, wcc.RED, wcc.YELLOW],
                [wcc.BLACK, wcc.BLUE, wcc.RED],
                [wcc.BLACK, wcc.RED, wcc.BLUE],
                [wcc.YELLOW, wcc.RED, wcc.BLUE],
                [wcc.RED, wcc.BLUE, wcc.BLUE],
                [wcc.RED, wcc.WHITE, wcc.WHITE],
                [wcc.GREEN, wcc.YELLOW, wcc.PINK],
                [wcc.WWHITE, wcc.BLACK, wcc.BLACK],
                [wcc.BLACK, wcc.Color(30,30,30), wcc.Color(30,30,30)]]
        self.color_mode_pos = 0
        self.rb_pos = 0 # index position for "rainbow"-mode
        try:
            self.brightness_mode_pos = config.getint('wordclock_display', 'brightness')
        except:
            print('WARNING: Brightness value not set in config-file: To do so, add a "brightness" between 1..255 to the [wordclock_display]-section.')
            self.brightness_mode_pos = 255

        try:
            self.brightness_use_sensor = config.getboolean('wordclock_display', 'useBrightnessSensor')            
        except:
            print('Not found brigtness sensor value ')
            self.brightness_use_sensor = False

        print('Using brigtness sensor : ' + str(self.brightness_use_sensor))
        if self.brightness_use_sensor:
            print('Importing sensor Library ')
            import Adafruit_GPIO.I2C as I2C
            address = 0x39 ## Device address
            self.i2c = I2C.Device(address,1)

        self.brightness_change = 8

    def run(self, wcd, wci):
        '''
        Displays time until aborted by user interaction on pin button_return
        '''
        # Some initializations of the "previous" minute
        prev_min = -1
        if self.brightness_use_sensor:                                
            control_on = 0x03 ## "On" value
            control_off = 0x00 ## "Off" value
            
            sensorMin = 0.0
            sensorMax = 100.0

            sensorCurrent = 120.0

            brightnessMin = 50.0
            brightnessMax = 255.0

            try:
                self.i2c.write8(0x00, control_on)
            except IOError as e:
                print(e)
            time.sleep(0.2)
            self.brightness_mode_pos = min(((((brightnessMax - brightnessMin) / sensorMax) * sensorCurrent) + brightnessMin),255)

        while True:
            # Get current time
            now = datetime.datetime.now()
            if self.brightness_use_sensor:                 
                newBrightness = self.brightness_mode_pos
                try:
                    sensorCurrent = float(self.i2c.readU16(0x8C))
                    #print('sensorCurrent is ' + str(sensorCurrent))
                    newBrightness = min(((((brightnessMax - brightnessMin) / sensorMax) * sensorCurrent) + brightnessMin),255)
                    newBrightness = int(newBrightness)
                except IOError as e:
                    print(e)
                time.sleep(0.2)
                #print('newBrightness is ' + str(newBrightness))
                                
            # Check, if a minute has passed (to render the new time)
            if prev_min < now.minute:                
                # Set background color
                self.show_time(wcd, wci)
                prev_min = -1 if now.minute == 59 else now.minute
            if self.brightness_use_sensor and newBrightness != self.brightness_mode_pos:                
                self.brightness_mode_pos = newBrightness            
                self.show_time(wcd, wci)                                

            event = wci.waitSecondsForEvent([wci.button_left, wci.button_return, wci.button_right], 2)
            # Switch display color, if button_left is pressed
            if (event == wci.button_left):
                self.color_mode_pos += 1
                if self.color_mode_pos == len(self.color_modes):
                    self.color_mode_pos = 0
                self.bg_color     = self.color_modes[self.color_mode_pos][0]
                self.word_color   = self.color_modes[self.color_mode_pos][1]
                self.minute_color = self.color_modes[self.color_mode_pos][2]
                self.show_time(wcd, wci)
                time.sleep(0.2)
            if (event == wci.button_return):
                return # Return to main menu, if button_return is pressed
            if (event == wci.button_right):
                time.sleep(wci.lock_time)
                self.color_selection(wcd, wci)

    def show_time(self, wcd, wci):
        now = datetime.datetime.now()
        # Set background color
        wcd.setColorToAll(self.bg_color, includeMinutes=True)
        # Returns indices, which represent the current time, when beeing illuminated
        taw_indices = self.taw.get_time(now)
        if self.typewriter and now.minute%5 == 0:
            for i in range(len(taw_indices)):
                wcd.setColorBy1DCoordinates(wcd.strip, taw_indices[0:i+1], self.word_color)
                wcd.show()
                time.sleep(1.0/self.typewriter_speed)
            wcd.setMinutes(now, self.minute_color)
            wcd.setBrightness(self.brightness_mode_pos)
            wcd.show()
        else:
            wcd.setColorBy1DCoordinates(wcd.strip, taw_indices, self.word_color)
            wcd.setMinutes(now, self.minute_color)
            wcd.setBrightness(self.brightness_mode_pos)
            wcd.show()

    def color_selection(self, wcd, wci):
        while True:
            # BEGIN: Rainbow generation as done in rpi_ws281x strandtest example! Thanks to Tony DiCola for providing :)
            if self.rb_pos < 85:
                self.word_color = self.minute_color = wcc.Color(3*self.rb_pos, 255-3*self.rb_pos, 0)
            elif self.rb_pos < 170:
                self.word_color = self.minute_color = wcc.Color(255-3*(self.rb_pos-85), 0, 3*(self.rb_pos-85))
            else:
                self.word_color = self.minute_color = wcc.Color(0, 3*(self.rb_pos-170), 255-3*(self.rb_pos-170))
            # END: Rainbow generation as done in rpi_ws281x strandtest example! Thanks to Tony DiCola for providing :)
            #TODO: Evaluate taw_indices only every n-th loop (saving ressources)
            now = datetime.datetime.now() # Set current time
            taw_indices = self.taw.get_time(now)
            wcd.setColorToAll(self.bg_color, includeMinutes=True)
            wcd.setColorBy1DCoordinates(wcd.strip, taw_indices, self.word_color)
            wcd.setMinutes(now, self.minute_color)
            wcd.show()
            self.rb_pos += 1
            if self.rb_pos == 256: self.rb_pos = 0
            event = wci.waitSecondsForEvent([wci.button_return, wci.button_left, wci.button_right], 0.1)
            if event > 0:
                time.sleep(wci.lock_time)
                break
        if not self.brightness_use_sensor:
            while True:
                self.brightness_mode_pos += self.brightness_change
                #TODO: Evaluate taw_indices only every n-th loop (saving ressources)
                now = datetime.datetime.now() # Set current time
                taw_indices = self.taw.get_time(now)
                wcd.setColorToAll(self.bg_color, includeMinutes=True)
                wcd.setColorBy1DCoordinates(wcd.strip, taw_indices, self.word_color)
                wcd.setMinutes(now, self.minute_color)
                wcd.setBrightness(self.brightness_mode_pos)
                wcd.show()
                if self.brightness_mode_pos < abs(self.brightness_change) or self.brightness_mode_pos > 255 - abs(self.brightness_change):
                    self.brightness_change *= -1
                event = wci.waitSecondsForEvent([wci.button_return, wci.button_left, wci.button_right], 0.1)
                if event > 0:
                    time.sleep(wci.lock_time)
                    return

