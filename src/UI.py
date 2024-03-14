from Config import WINDOW_PROPERTIES

class Button:
    def __init__(self, image, scale = 1, xy = None, padding=None, background = None):
        width = image.get_width()
        height = image.get_height()
        self.image = pygame.transform.scale(image, (int(width*scale), int(height*scale)))

        self.background = background

        if background:
            self.background = pygame.transform.scale(background,
                                    (   int(background.get_width()*scale),
                                        int(background.get_height()*scale)
                                    )
                                )
            self.rectangle = self.background.get_rect()

        else:
            self.rectangle = self.image.get_rect()

        if xy:
            self.rectangle.topleft = (xy[0],xy[1])
        elif padding:
            if background:
                self.rectangle.topleft = (
                    WINDOW_PROPERTIES.SCREEN_WIDTH//2 - int(background.get_width()*scale)//2 - padding[0],
                    WINDOW_PROPERTIES.SCREEN_HEIGHT//2 - int(background.get_height()*scale)//2 - padding[1]
                )
            else:
                self.rectangle.topleft = (
                    WINDOW_PROPERTIES.SCREEN_WIDTH//2 - int(width*scale)//2 - padding[0],
                    WINDOW_PROPERTIES.SCREEN_HEIGHT//2 - int(height*scale)//2 - padding[1]
                )
        else:
            self.rectangle.topleft = (0,0)

        # set image center in background
        if background:
            self.imageRect = self.image.get_rect()
            self.imageRect.center = self.rectangle.center

        self.clicked = False

    def draw(self, surface, mousePosition, mouse):
        action = False

        if self.rectangle.collidepoint(mousePosition):
            if mouse == 1 and self.clicked== False:
                self.clicked = True
                action = True

        if mouse == 0:
            self.clicked = False

        if self.background:
            surface.blit(self.background, (self.rectangle.x, self.rectangle.y))
            surface.blit(self.image, self.imageRect)
        else:
            surface.blit(self.image, (self.rectangle.x, self.rectangle.y))
        return action

class Slider:
  def __init__(self,
    position: tuple, size: tuple, initValue: float,
    minValue: int, maxValue: int, containerBackground=None,
    padding=(0,0)):

    self.leftPosition = position[0]
    self.topPosition = position[1]
    self.rightPosition = position[0] + size[0]

    self.size = size

    self.min = minValue
    self.max = maxValue

    self.initialValue = (self.rightPosition - self.leftPosition) * initValue

    self.containerRect = pygame.Rect(self.leftPosition, self.topPosition, self.size[0], self.size[1])
    self.buttonRect = pygame.Rect(self.leftPosition, self.topPosition, self.initialValue, self.size[1] - padding[1]//2)

    self.containerBackground = containerBackground
    self.padding = padding
    self.containerBackgroundRect = None

    if containerBackground:
      self.containerBackground = pygame.transform.scale(containerBackground, (self.containerRect.width + padding[0], self.containerRect.height + padding[1]))
      self.containerBackgroundRect = self.containerBackground.get_rect()
      self.containerBackgroundRect.center = self.containerRect.center

  def draw(self, surface, displayValue=False, font=None, textColor=TEXT_COLOR):
    if self.containerBackground:
      surface.blit(self.containerBackground, (self.containerBackgroundRect.x , self.containerBackgroundRect.y))
    else:
      pygame.draw.rect(surface, "green", self.containerRect)

    pygame.draw.rect(surface, "darkgrey", self.buttonRect)

    if displayValue:
      drawTextOnScreen(
        surface,
        str(self.getValue()),
        font,
        textColor,
        self.containerRect.right + FONT.FONTSIZE["SLIDER_FONT_SIZE"],
        self.containerRect.top
      )

  def update(self, mousePosition, mouse):
    if self.containerRect.collidepoint(mousePosition) and mouse:
      # self.buttonRect.centerx = mousePosition[0]
      self.buttonRect = pygame.Rect(self.leftPosition, self.topPosition, mousePosition[0] - self.leftPosition, self.size[1] - self.padding[1]//2)

  def getValue(self, padding = (1,0)):
    valueRange = self.rightPosition - self.leftPosition - padding[0] - padding[1]
    buttonPosition = self.buttonRect.centerx - self.leftPosition

    # TODO: NORMALIZATION
    return int((buttonPosition/valueRange)*(self.max-self.min)*2+self.min)

class Menu:
    def __init__(self, buttons , sliders = [], images = [], imagesPosition = [], menuBackground=None, size = (500,500), xy = None):

        self.menuBackground = menuBackground

        self.size = size
        if xy:
            self.x = xy[0]
            self.y = xy[1]
        elif menuBackground:
            #center align
            self.x = WINDOW_PROPERTIES.SCREEN_WIDTH // 2 - menuBackground.get_width() // 2
            self.y = WINDOW_PROPERTIES.SCREEN_HEIGHT // 2 - menuBackground.get_height() // 2
        else:
            #center align
            self.x = WINDOW_PROPERTIES.SCREEN_WIDTH // 2 - size[0] // 2
            self.y = WINDOW_PROPERTIES.SCREEN_HEIGHT // 2 - size[1] // 2

        self.isDisplay = False
        self.buttonsValue = [False] * len(buttons)
        self.buttons = buttons
        self.sliders = sliders
        self.images = images
        self.imagesPosition = imagesPosition

        self.slidersValue = None
        if sliders: self.slidersValue = [slider.getValue() for slider in sliders]

    # draw buttons, also get buttons value
    def draw(self, surface, mousePosition, mouse,backgroundColor = None, border = 0, sliderFont = None):
        if self.isDisplay:

            # draw background
            if self.menuBackground:
                surface.blit(self.menuBackground, (self.x, self.y))
            elif backgroundColor:
                pygame.draw.rect(surface, backgroundColor, (self.x, self.y, self.size[0], self.size[1]) , border)

            for i in range(len(self.images)):
                surface.blit(self.images[i], self.imagesPosition[i])

            for i in range(len(self.sliders)):
                self.sliders[i].update(mousePosition, mouse)
                self.sliders[i].draw(surface, displayValue=True, font=sliderFont)
                self.slidersValue[i] = self.sliders[i].getValue()

            for i in range(len(self.buttons)):
                self.buttonsValue[i] = self.buttons[i].draw(surface, mousePosition, mouse)


        return {
            "buttons": self.buttonsValue,
            "sliders": self.slidersValue,
        }

    def setButtonValue2False(self, buttonIndex = None, value=False):
        if buttonIndex:
            self.buttonsValue[buttonIndex] = value
        else:
            self.buttonsValue = [value] * len(self.buttons)

    def setIsDisplay(self, value):
        self.isDisplay = value

    def getIsDisplay(self):
        return self.isDisplay

    def setImage(self, image, index):
        self.images[index] = image