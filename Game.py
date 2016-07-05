import sys, pygame
import queue
import random
import time
import shelve

platBuffer = 5 # amount of platforms instantiated at once
displayHeight = 720 # window height
displayWidth = 1280 # window width
runSpeed = 8 # movement speed

pygame.init() # initialize pygame

pygame.mixer.music.load('assets/music/menu.ogg') # load menu music
screen = pygame.display.set_mode((displayWidth,displayHeight)) # screen
title = pygame.image.load('assets/images/title.png').convert_alpha() # main menu title

backgroundImage = pygame.image.load('assets/images/sky.png').convert_alpha() # background sky
buildingsFar = pygame.image.load('assets/images/buildingsFar.png').convert_alpha() # further buildings
buildingsClose = pygame.image.load('assets/images/buildingsClose.png').convert_alpha() # closer buildings
lasersImage = pygame.image.load('assets/images/lasers.png').convert_alpha() # background lasers

ship = pygame.image.load('assets/images/ship.png').convert_alpha() # moving ship
shipLaser1 = pygame.image.load('assets/images/shipLaser1.png').convert_alpha() # moving ship laser
shipLaser2 = pygame.image.load('assets/images/shipLaser2.png').convert_alpha() # moving ship laser
shipLaser3 = pygame.image.load('assets/images/shipLaser3.png').convert_alpha() # moving ship laser
shipLaser4 = pygame.image.load('assets/images/shipLaser4.png').convert_alpha() # moving ship laser

clock = pygame.time.Clock() # used for framerate

# platforms player jumps on
class Platform():
    # stores parameters as pygame rectangle
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect((x,y),(width,height))
     
    # draws black rectangle
    def draw(self):
        pygame.draw.rect(screen,(0,0,0), self.rect)
        
    # moves the rectangle and stores new position
    def update(self):
        self.rect = self.rect.move(-runSpeed,0)

# player 
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__() # call parent constructor
        self.jumping = False # on platform or in air
        self.holding = False # holding jump key
        self.dead = False # if player fell or not
        self.groundDelay = 0.03 # ground animation speed 
        self.airDelay = 0.1 # air animation speed
        self.animDelay = self.groundDelay # initialize animation speed   
        self.start = time.time() # initializes a timer
        
        self.images = [] # list to store player images
        for i in range(12):
            self.images.append(pygame.image.load('assets/player/'+str(i)+'.png').convert_alpha()) # append images
            self.images[i] = pygame.transform.scale(self.images[i], (75, 100)) # scale images

        self.rect = pygame.Rect(100, 428, 75, 100) # initialize player position
        self.pIndex = 0 # initializes current sprite image index
        self.move_x = 0 # rate of moving on x axis
        self.move_y = 0 # rate of moving on y axis

    # updates player traits, called with Group.update()
    def update(self, gap):
        self.rect.y += self.move_y # changes player y position
        self.rect.x += self.move_x # changes player x position
        if self.holding and self.move_y < 0: # if holding jump and moving upwards
            self.gravity(gap, 0.25) # lower gravity 
        else: # falling
            self.gravity(gap, 0.55) # normal gravity

        # set animation delay
        if not self.jumping and not self.dead and self.animDelay != self.groundDelay: # moving on platform
            self.animDelay = self.groundDelay
        elif self.animDelay != self.airDelay: # moving in air
            self.animDelay = self.airDelay
                 
        if time.time() - self.start >= self.animDelay: # animation speed
            self.pIndex = (self.pIndex+1) % len(self.images) # changes to next image
            self.start = time.time() # reset timer

        self.image = self.images[self.pIndex] # sets current sprite image     

    # sets gravity for different scenarios 
    def gravity(self, gap, grav):
        if (gap or self.jumping) and not self.dead: # if player is in the air 
            self.move_y += grav # sets downward move rate
            if self.rect.y >= 428: # if player is level or below top of platforms
                if gap: # player is not on a platform 
                    self.move_x = -runSpeed # player moves with platforms
                    self.move_y = 10 # player falls fast
                    self.dead = True # player is dead
                else: # player is on platform
                    self.rect.y = 428 # saftey, ensures player stays level with top of platforms
                    self.move_y = 0 # not moving up or down
                self.jumping = False # not jumping
        if self.move_y > 10: # fall rate limit
            self.move_y = 10

    # adds upward movement rate when called
    def jump(self):
        if not self.jumping and not self.dead: # player is not currently jumping and not dead
            self.move_y = -10 # sets rate of moving
            self.jumping = True # sets jump state as true when called

    # stores state of player holding key
    def holdKey(self, holding):
        self.holding = holding

    # returns if player is dead
    def isDead(self):
        return self.dead

    # resets player variables for new game
    def resetPlayer(self):
        self.dead = False
        self.rect.x = 100
        self.rect.y = 428
        self.move_y = 0
        self.move_x = 0
                            
class Main:
    def __init__(self):
        pygame.display.set_caption('Runner') # game window title
        
        d = shelve.open('assets/score/scorefile') # open score file
        try: # highscore has been recorded before
            self.highsc = d['score'] # initialize session highscore to saved highscore
        except (KeyError): # no score recorded yet
            self.highsc = 0 # initialize session highscore to 0
            d['score'] = 0 # create highscore save
        d.close() # close score file
        self.score = 0 # initialize score counter
        
        self.backdrop = [buildingsFar]*2 # list of two further building image to loop around
        self.backdrop2 = [buildingsClose]*2 # list of two closer building image to loop around
        self.lasers = [lasersImage]*2 # background lasers
        self.laserTimer = time.time() # timer for flickering lasers
        self.shipLaserTimer = time.time() # timer for switching ship's laser images
        self.laserSet = False # has a laser image been assigned to moving ship
        self.buildingsFar1Pos = 0 # initialize further buildings image x position 
        self.buildingsFar2Pos = buildingsFar.get_width() # initialize second further buildings image x position 
        self.buildingsClose1Pos = 0 # initialize closer buildings image x position 
        self.buildingsClose2Pos = buildingsClose.get_width() # initialize second closer buildings image x position 
        self.shipX = -200 # initialize moving ship's x position
        self.shipY = 150 # initialize moving ship's y position
        self.shipSpeed = 10 # initialize moveing ship's speed
        self.shipLasers = [shipLaser1,shipLaser2,shipLaser3,shipLaser4] # list of moving ship's lasers in different directions

        self.gap = False # keeps track of gaps between platforms
        self.lastPlat = platBuffer-1 # points to current furthest platform
        self.currentPlat = 0 # points to platform under player
        self.platSet = False # remembers if currentPlat was incremented 

        self.endTimer = 0 # after death timer
        self.isPaused = False # game is paused
        self.menuSet = False # menu has been displayed
        self.isMain = True # on main menu
        self.color1Set = False # color when option1 is clicked
        self.color2Set = False # color when option2 is clicked
        self.musicLoaded = False # is music loaded with pygame
        
        player = Player() # instantiate player
        playerGroup = pygame.sprite.Group(player) # sets varibale for player sprite group in order to call update
        playerGroup.update(self.gap) # first update
        self.platList = [] # initialize list for storing platforms
        self.createPlats(platBuffer) # create and store platforms

        # game loop    
        while True:
            for event in pygame.event.get(): # event handler
                if event.type == pygame.KEYDOWN: # key down
                    if event.key == pygame.K_SPACE: # spacebar -> jump
                        player.holdKey(True) # user is holding spacebar
                        player.jump()
                    if event.key == pygame.K_ESCAPE: # escape key -> isPaused/unisPaused
                        if not self.isPaused and not self.isMain: # ensures cannot pause twice or in main menu
                            self.isPaused = True
                            pygame.mixer.music.set_volume(0.1) # volume lowered when paused
                        else:
                            self.isPaused = False
                            pygame.mixer.music.set_volume(1) # volume back to normal
                            
                if event.type == pygame.KEYUP: # key up
                    if event.key == pygame.K_SPACE: # spacebar up
                        player.holdKey(False) # user released spacebar
                        
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # clicked mouse
                    pos = pygame.mouse.get_pos() # xy position of mouse
                    pygame.mouse.get_pressed()[0]
                    if self.isPaused: # game is paused
                        self.pausedMenu(True,False,pos) # call menu and pass button down mouse pos
                    else:
                        self.mainMenu(True,False,pos) # call menu
                        
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1: # released mouse
                    pos = pygame.mouse.get_pos() # xy position of mouse
                    if self.isPaused: # game is paused
                        self.pausedMenu(False,True,pos)
                    else: 
                        self.mainMenu(False,True,pos) # call menu and pass button up mouse pos
                        
                if event.type == pygame.QUIT: # handles closing game
                    pygame.quit() # quit pygame
                    sys.exit() # exit system
                    break # break from game loop
            
            # runs game if player is alive
            if (not player.isDead() or (self.endTimer > 0 and time.time() - self.endTimer < 1)) and not self.isPaused and not self.isMain: # stops game after delay
                self.game(playerGroup)
            elif player.isDead() and self.endTimer == 0: # start delay timer if player dies
                self.endTimer = time.time()
            elif not self.isPaused and not self.isMain: # reset the game
                self.setHighscore() # checks/sets highscore
                self.resetGame()
                player.resetPlayer()

            # control main menu
            if self.isMain:
                self.mainMenu(False,False,None)

            # control paused menu
            if self.isPaused and not self.menuSet: # only draws menu options once
                self.pausedMenu(False,False,None)
                self.menuSet = True
            elif not self.isPaused and self.menuSet:
                self.menuSet = False

            clock.tick(120) # update speed
            pygame.display.update() # updates display

    # main menu screen
    def mainMenu(self,down,up,pos):
        if not self.musicLoaded: # checks weather or not music has been loaded
            pygame.mixer.music.load('assets/music/menu.ogg') # load menu music
            pygame.mixer.music.play(-1) # play and loop music
            self.musicLoaded = True # remember music is loaded
        
        color1 = (200,200,200) # default white
        color2 = (200,200,200) # default white
        if down: # mouse button down
            x = pos[0] # mouse x position
            y = pos[1] # mouse y position
            if x > 580 and x <700 and y > 300 and y < 355: # mouse is over resume button
                self.color1Set = True # yellow if clicked
            if x > 590 and x <670 and y > 400 and y < 435: # mouse is over quit button
                self.color2Set = True # yellow if clicked
        if up: # mouse button up
            self.color1Set = False # back to white
            self.color2Set = False # back to white
            x = pos[0] # mouse x position
            y = pos[1] # mouse y position
            if x > 580 and x <700 and y > 300 and y < 355: # mouse is over resume button
                self.musicLoaded = False # allows game to set music
                self.isMain = False
                self.resetGame()
            if x > 590 and x <670 and y > 400 and y < 435: # mouse is over quit button
                pygame.quit() # quit game
                sys.exit() # exit system

        if self.color1Set:
            color1 = (200,200,0) # yellow if clicked
        if self.color2Set:
            color2 = (200,200,0) # yellow if clicked

        self.setScenery() # sets position of scenery
        self.drawScenery() # moving scenery

        font1 = pygame.font.Font(None, 80) # set large font
        font2 = pygame.font.Font(None, 50) # set small font
        font3 = pygame.font.Font(None, 24) # set small font
        
        screen.blit(title, (0,0)) # display title on screen

        play = font1.render("Play", 1, color1)
        screen.blit(play, (displayWidth/2-58,300)) # display play on screen

        quitgame = font2.render("Quit", 1, color2)
        screen.blit(quitgame, (displayWidth/2-40,400)) # display quit on screen

        info = font3.render("Developed by Eric Svitok", 1, (200,200,200))
        screen.blit(info, (displayWidth/2-98,displayHeight-20)) # made by me

    # game screen
    def game(self, playerGroup):
        if not self.musicLoaded: # checks weather or not music has been loaded
            pygame.mixer.music.load('assets/music/game.ogg') # load game music
            pygame.mixer.music.play(-1) # play and loop music
            self.musicLoaded = True # remember music is loaded

        self.setScenery() # sets position of scenery
        self.drawScenery() # moving scenery
        
        for i in range(platBuffer): # iterates through platforms
            if self.platEnd(i) < 0: # platform at index passes left of screen
                self.resetPlat(i) # reset platform at index
            self.platList[i].draw() # draws platform at index
            self.platList[i].update() # updates platform at index
            
        self.setPlatIndex() 
        self.setGap() 
        self.displayScore(self.score)
        playerGroup.update(self.gap)
        playerGroup.draw(screen)

    # pause screen
    def pausedMenu(self, down, up, pos):
        color1 = (200,200,200) #white by default
        color2 = (200,200,200) #white by default
        color3 = (200,200,200) #white by default
        
        if down: # mouse button down
            x = pos[0] # mouse x position
            y = pos[1] # mouse y position
            if x > 565 and x <710 and y > 230 and y < 260: # mouse is over resume button
                color1 = (200,200,0)
            if x > 550 and x <735 and y > 330 and y < 360: # mouse is over menu button
                color2 = (200,200,0)
            if x > 590 and x <670 and y > 430 and y < 460: # mouse is over quit button
                color3 = (200,200,0)
        if up: # mouse button up
            x = pos[0] # mouse x position
            y = pos[1] # mouse y position
            if x > 565 and x <710 and y > 230 and y < 260: # mouse is over resume button
                self.isPaused = False
                pygame.mixer.music.set_volume(1) # volume back to normal
            if x > 550 and x <735 and y > 330 and y < 360: # mouse is over menu button
                self.musicLoaded = False # allows menu to set music
                self.isMain = True # on main menu
                self.isPaused = False # no longer paused
                pygame.mixer.music.set_volume(1) # volume back to normal
            if x > 590 and x <670 and y > 430 and y < 460: # mouse is over quit button
                pygame.quit() # quit game
                sys.exit() # exit system           
        
        font = pygame.font.Font(None, 50) # set font

        resume = font.render("Resume", 1, color1)
        screen.blit(resume, (displayWidth/2-70,230)) # display resume on screen

        main = font.render("Main Menu", 1, color2)
        screen.blit(main, (displayWidth/2-90,330)) # display main menu on screen

        quitgame = font.render("Quit", 1, color3)
        screen.blit(quitgame, (displayWidth/2-45,430)) # display quit on screen

    # moving background images
    def drawScenery(self):
        screen.blit(backgroundImage,[0,0]) # updates background every frame
        
        if time.time() - self.laserTimer > 0.1:
            screen.blit(self.lasers[0],[self.buildingsFar1Pos,0]) # updates background lasers
            screen.blit(self.lasers[1],[self.buildingsFar2Pos,0]) # updates background lasers
            if time.time() - self.laserTimer > random.uniform(0,1): # flashes lasers at random rate
                self.laserTimer = time.time()
        
        screen.blit(self.backdrop[0],[self.buildingsFar1Pos,0]) # draws further background buildings
        screen.blit(self.backdrop[1],[self.buildingsFar2Pos,0]) # draws further background buildings

        if not self.laserSet: # if new laser has not been set
            self.laserChoice = random.choice(self.shipLasers) # chooses random laser direction
            self.laserSet = True # has been set
        if self.shipX >= -100: # if ship position is about to be on screen
            screen.blit(self.laserChoice,[self.shipX-730,self.shipY-730]) # draw ship's lasers
            screen.blit(ship,[self.shipX,self.shipY]) # draw ship
        if time.time() - self.shipLaserTimer > random.uniform(0,2): # flashes ship's lasers at random rate
            self.shipLaserTimer = time.time() # reset timer
            self.laserSet = False # has not been set

        screen.blit(self.backdrop2[0],[self.buildingsClose1Pos,0]) # draws closer background buildings
        screen.blit(self.backdrop2[1],[self.buildingsClose2Pos,0]) # draws closer background buildings
        
    # instantiates and appends platforms to list
    def createPlats(self, buffer):
        for i in range(buffer):
            newPlat = Platform(self.platEnd(i-1), displayHeight/1.4, 400, displayHeight/2.5) # instantiates platforms back to back
            self.platList.append(newPlat) # append platform instance to list

    # moves passed platforms to the end and changes size/spacing
    def resetPlat(self, index):
        self.platList[index].rect.width = random.randint(200,800) # sets random platform width
        self.platList[index].rect.x = self.platEnd(self.lastPlat) + random.randint(100,550) # places at end at random distance from the platform ahead
        self.lastPlat = index # sets lastPlat pointer to index of moved platform

    # determines if player is over a gap
    def setGap(self):
        if self.platStart(self.currentPlat) < 100 and self.platEnd(self.currentPlat) > 100 and self.gap:
            self.gap = False # player is on a platform
        elif self.platEnd(self.currentPlat) < 100 and not self.gap: # if player completely passes platform
            if self.platStart((self.currentPlat+1)%platBuffer) > 100: # ensures there is no immediate platform
                self.gap = True # player is in between platforms
                self.score += 1 # increment score
            self.platSet = False # new plat needs to be set
            
    # gets position of beginning of a platform at specified index               
    def platEnd(self, index):
        if len(self.platList) > 0: # makes sure list contains an object
            return self.platList[index].rect.x + self.platList[index].rect.width
        else: # returns 0 if list is empty
            return 0 

    # gets position of beginning of a platform at specified index
    def platStart(self, index):
        if len(self.platList) > 0: # makes sure list contains an object
            return self.platList[index].rect.x
        else: # returns 0 if list is empty
            return 0

    # sets index of next platform under player
    def setPlatIndex(self):
        if self.platEnd(self.currentPlat) < 100 and not self.platSet:
            self.currentPlat = (self.currentPlat+1)%platBuffer # increments platform index (circular)
            self.platSet = True # ensures currentPlat increments only once per call

    # stores and and moves positioning of background scenery
    def setScenery(self):
        if self.buildingsFar1Pos <= -buildingsFar.get_width(): # loops furthest buildings
            self.buildingsFar1Pos = buildingsFar.get_width()
        if self.buildingsFar2Pos <= -buildingsFar.get_width(): # loops furthest buildings
            self.buildingsFar2Pos = buildingsFar.get_width()
        if self.buildingsClose1Pos <= -buildingsClose.get_width(): # loops closer buildings
            self.buildingsClose1Pos = buildingsClose.get_width()
        if self.buildingsClose2Pos <= -buildingsClose.get_width(): # loops closer buildings
            self.buildingsClose2Pos = buildingsClose.get_width()
        if self.shipX >= displayWidth: # loops moving ship 
            self.shipSpeed = random.randint(2,10) # random ship speed
            self.shipY = random.randint(150,600) # random ship height
            self.shipX = random.randint(-3000,-100) # random reset point
        self.buildingsFar1Pos -= 1 # move furthest buildings
        self.buildingsFar2Pos -= 1 # move furthest buildings
        self.buildingsClose1Pos -= 4 # move closer buildings
        self.buildingsClose2Pos -= 4 # move closer buildings
        self.shipX += self.shipSpeed # move ship

    # shows score (number of platforms passed)
    def displayScore(self, score):
        font = pygame.font.Font(None, 28)
        sc = font.render("Score: " + str(score), 1, (125,125,0))
        if score > self.highsc: # current score passes highscore
            highsc = font.render("Highest: " + str(score), 1, (125,125,0)) # display highscore as current score
        else: # current score is below highscore
            highsc = font.render("Highest: " + str(self.highsc), 1, (125,125,0))# display highscore
        screen.blit(sc, (27,5)) # display score on screen
        screen.blit(highsc, (10,23)) # display highscore on screen

    # stores highscore
    def setHighscore(self):
        d = shelve.open('assets/score/scorefile') # opens .dat file
        if self.score > d['score']: # if current score is highest ever
            d['score'] = self.score # record new highscore
            self.highsc = d['score'] # updates session highscore with saved highscore
        d.close() # close .dat file

    # resets variables to play from start
    def resetGame(self):
        self.score = 0 
        self.endTimer = 0
        self.gap = False
        self.lastPlat = platBuffer-1
        self.currentPlat = 0
        del self.platList[:] # removes old platforms
        self.createPlats(platBuffer) # creates new platforms
        #print("Game Reset")
Main()
