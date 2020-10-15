# Import libraries
import RPi.GPIO as GPIO
import random
import ES2EEPROMUtils
import os
import time
import sys

# some global variables that need to change as we run the program
end_of_game = None  # set if the user wins or ends the game
begin = 0
end = 0
buttonStatus = 0
guesses = 0


# DEFINE THE PINS USED HERE
LED_value = [11, 13, 15]
LED_accuracy = 32
btn_submit = 16
btn_increase = 18
buzzer = 33
LED_pwm = ""
buzzer_pwm = ""
eeprom = ES2EEPROMUtils.ES2EEPROM()


# Print the game banner
def welcome():
    os.system('clear')
    print("  _   _                 _                  _____ _            __  __ _")
    print("| \ | |               | |                / ____| |          / _|/ _| |")
    print("|  \| |_   _ _ __ ___ | |__   ___ _ __  | (___ | |__  _   _| |_| |_| | ___ ")
    print("| . ` | | | | '_ ` _ \| '_ \ / _ \ '__|  \___ \| '_ \| | | |  _|  _| |/ _ \\")
    print("| |\  | |_| | | | | | | |_) |  __/ |     ____) | | | | |_| | | | | | |  __/")
    print("|_| \_|\__,_|_| |_| |_|_.__/ \___|_|    |_____/|_| |_|\__,_|_| |_| |_|\___|")
    print("")
    print("Guess the number and immortalise your name in the High Score Hall of Fame!")


# Print the game menu
def menu():
    global end_of_game
    option = input("Select an option:   H - View High Scores     P - Play Game       Q - Quit\n")
    option = option.upper()
    if option == "H":
        os.system('clear')
        print("HIGH SCORES!!")
        s_count, ss = fetch_scores()
        display_scores(s_count, ss)
    elif option == "P":
        os.system('clear')
        print("Starting a new round!")
        print("Use the buttons on the Pi to make and submit your guess!")
        print("Press and hold the guess button to cancel your game")
        value = generate_number()
        while not end_of_game:
            
            pass
    elif option == "Q":
        print("Come back soon!")
        exit()
    else:
        print("Invalid option. Please select a valid one!")


class Counter():
    def __init__(self):
        self.cnt = 0

    def increment(self):
        self.cnt += 1

    def reset(self):
        self.cnt = 0

    def get_value(self):
        return self.cnt


GPIO.setmode(GPIO.BOARD)
LED_pwm = GPIO.PWM(LED_accuracy, 1000)
buzzer_pwm = GPIO.PWM(buzzer, 1000)
count = Counter()


def display_scores(count, raw_data):
    # print the scores to the screen in the expected format
    print("There are {} scores. Here are the top 3!".format(count))
    # print out the scores in the required format
    scores = raw_data
    if (count == 0):
        print("sadly there are non :(")
    else:
        scores.sort(key=sort_list)                    #sort list
        i = 0
        for entry in scores:
            if (i == 3):
                break
            print("{} - {} took {} guesses".format((i + 1),entry[0],entry[1]))
            i += 1
    pass


def callback1(channel):
    btn_guess_pressed()
    print("falling edge detected on btn_submit")
    pass


def callback2(channel):
    btn_increase_pressed()
    print("falling edge detected on btn_increase")
    pass


# Setup Pins
def setup():
    
    GPIO.setup(LED_value[0], GPIO.OUT)
    GPIO.setup(LED_value[1], GPIO.OUT)
    GPIO.setup(LED_value[2], GPIO.OUT)
    GPIO.setup(LED_accuracy, GPIO.OUT)
    GPIO.setup(buzzer, GPIO.OUT)
    GPIO.setup(btn_submit, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(btn_increase, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    GPIO.output(LED_value[0], GPIO.LOW)
    GPIO.output(LED_value[1], GPIO.LOW)
    GPIO.output(LED_value[2], GPIO.LOW)
    GPIO.output(buzzer, GPIO.LOW)
    eeprom.populate_mock_scores()
    
    LED_pwm.start(0)
    buzzer_pwm.start(0)
    GPIO.add_event_detect(btn_submit, GPIO.BOTH, callback=callback1, bouncetime=500)
    GPIO.add_event_detect(btn_increase, GPIO.FALLING, callback=callback2, bouncetime=500)
    # Setup debouncing and callbacks
    pass


# Load high scores
def fetch_scores():
    # get however many scores there are
    
    score_count = eeprom.read_byte(0)                         #Read 1st register to find num scores
    print("amount of scores is: {}" .format(score_count))
    
    # Get the scores
    scores_raw = []
    scores_raw = eeprom.read_block(1,score_count*4)         #get amount of scores
    # convert the codes back to ascii
    i = 0
    j = 0
    k = 0
    temp = ""                                               #initiate variables to use in loops
    rows, cols = (score_count, 2)                           #Create empty scores 2D list 
    scores = [[0 for i in range(cols)] for j in range(rows)]
    while (i < len(scores_raw)):                            #populate scores with 1st 3 char = name, 3th = score
        if (j == 3):                                        #once name has 3 letters add it to list
            scores[k][0] = temp
            scores[k][1] = scores_raw[i]                    #add next item in scores which will be num of guesses
            k = k + 1
            i = i + 1
            j = 0
            temp = ""
            continue
        temp = temp + chr(scores_raw[i])                    #add charachters to temp until its full
        i += 1
        j += 1
    # return back the results
    return score_count, scores                              #returns num of scores in score_count. return 2D list scores with name and score


# Save high scores
def save_scores(name, guess):
    score_count, scores = fetch_scores()           
    scores.append([name, guess])                   #include new score
    scores.sort(key=sort_list)                     #sort list
    score_write = []
    for name_entry in scores:                      #turn 2D scores into 1D raw data list to be sent to eeprom
        i = 0
        for x in name_entry:
            if (i == 0):
                j = 0
                while (j < 3):
                    score_write.append(ord(x[j]))   #transform name to ASCII value and add to score_write
                    j += 1
            else:
                score_write.append(x)
            i += 1
    print(score_write)
    score_count = score_count + 1               #increment amount of scores
    eeprom.write_byte(0,score_count)            #Update total scores in reg 0 in EEEPROM
    eeprom.write_block(1, score_write)          #write all scores to eeprom
    pass

def sort_list(elem):        #used when sorting lists
    return elem[1]

# Generate guess number
def generate_number():
    return random.randint(0, pow(2, 3)-1)


num = generate_number()


# Increase button pressed
def btn_increase_pressed():
    temp = count.get_value()
    GPIO.output(LED_value[0], temp & 0x01)
    GPIO.output(LED_value[1], temp & 0x02)
    GPIO.output(LED_value[2], temp & 0x04)
    count.increment()
    if count.get_value() > 7:
        count.reset()
    pass


# Guess button
def btn_guess_pressed():
    global num
    global guesses
    start_time = time.time()
    diff = 0
    while (GPIO.input(btn_submit) == 0) and (diff < 2):
        now_time = time.time()
        diff = - start_time + now_time
    if diff < 2:
        guesses += 1
        guess = count.get_value()
        # Compare the actual value with the user value displayed on the LEDs
        diff1 = guess - num
        diff1 = abs(diff1)
        accuracy_leds(diff1)
        trigger_buzzer(diff1)
        if diff1 == 0:
            GPIO.output(LED_value, GPIO.LOW)
            GPIO.output(LED_accuracy, GPIO.LOW)
            sguess = str(guesses)
            print("You Won in only " + sguess + " guesses!\n")
            name = input("Enter your name: ")
            while len(name) != 3:
                print("your name should be 3 letters long!\n")
                name = input("Try again!")
            print("name: {} guesses: {} " .format(name, guess))          
            save_scores(name, guess)
            os.execl(sys.executable, sys.executable, * sys.argv)
        elif diff1 == 1:
            print("off by 1")
        elif diff1 == 2:
            print("off by 2")
        elif diff1 == 3:
            print("off by 3")
    else:
        # If they've pressed and held the button, clear up the GPIO and take them back to the menu screen
        os.execl(sys.executable, sys.executable, * sys.argv)

    
    # Change the PWM LED
    # if it's close enough, adjust the buzzer
    # if it's an exact guess:
    # - Disable LEDs and Buzzer
    # - tell the user and prompt them for a name
    # - fetch all the scores
    # - add the new score
    # - sort the scores
    # - Store the scores back to the EEPROM, being sure to update the score count
    pass


# LED Brightness
def accuracy_leds(off):
    # temp = 
    # LED_pwm.ChangeDutyCycle(temp)
    # Set the brightness of the LED based on how close the guess is to the answer
    # - The % brightness should be directly proportional to the % "closeness"
    # - For example if the answer is 6 and a user guesses 4, the brightness should be at 4/6*100 = 66%
    # - If they guessed 7, the brightness would be at ((8-7)/(8-6)*100 = 50%
    pass

# Sound Buzzer
def trigger_buzzer(off):  # triggers being given a value by how far off it is
    if off == 0:
        GPIO.output(buzzer, GPIO.LOW)
    elif off == 1:
        buzzer_pwm.ChangeFrequency(4)
    elif off == 2:
        buzzer_pwm.ChangeFrequency(2)
    elif off == 3:
        buzzer_pwm.ChangeFrequency(1)
    else:
        GPIO.output(buzzer, GPIO.HIGH)
    pass


if __name__ == "__main__":
    try:
        # Call setup function
        setup()
        welcome()
        while True:
            menu()
            pass
    except Exception as e:
        print(e)
    finally:
        GPIO.cleanup()
