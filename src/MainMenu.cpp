#include "../include/MainMenu.hpp"


std::string opts[MAX_NUMBER_IN_MENU] = {
  "3D",
  "Original TITAN",
  "EXIT"
}; 

MainMenu::MainMenu(sf::RenderWindow& window):window(window){
  
  if(!font.loadFromFile(MENU_DEFAULT_FONT_PATH))
  {
    exit(32);
  }

  int currentPositionX = 0;
  int positionY = 0;
  
  for(int i=0; i< MAX_NUMBER_IN_MENU; i+=1)
  {
    this->menu[i].setFont(font);
    this->menu[i].setString(opts[i]);
    this->menu[i].setFillColor(TEXT_COLOR);
    this->menu[i].setCharacterSize(CHARACTER_SIZE);
     
    if(currentPositionX >= MENU_WIDTH)
    {
      currentPositionX = 0;
      positionY += (SPACING + CHARACTER_SIZE);
    }

    this->menu[i].setPosition(sf::Vector2f(currentPositionX, positionY));
    currentPositionX += (SPACING + this->menu[i].getLocalBounds().width);
  }
  this->selectedItem = 0;
}

void MainMenu::deselectAll(){
  for(int i=0; i < MAX_NUMBER_IN_MENU; i+=1)
  {
    this->menu[i].setFillColor(TEXT_COLOR);
  }
}

void MainMenu::setIsChoosing(bool value){
  this->isChoosing = value;
  if (!isChoosing)
  {
    this->deselectAll();
  }
  else 
  {
    this->setSelectedItem(this->selectedItem);
  }
}

void MainMenu::setSelectedItem(int item){
  this->menu[item].setFillColor(TEXT_COLOR_HOVER);
}

void MainMenu::moveRight(){
  if(this->isChoosing && this->selectedItem + 1 <  MAX_NUMBER_IN_MENU)
  {
    this->menu[selectedItem].setFillColor(TEXT_COLOR);
    this->selectedItem += 1;
    this->setSelectedItem(selectedItem);                    
  }
}

void MainMenu::moveLeft(){
  if (this->isChoosing && this->selectedItem - 1 >= 0) {
    this->menu[selectedItem].setFillColor(TEXT_COLOR);
    this->selectedItem -= 1;
    this->setSelectedItem(selectedItem);
  }
}

void MainMenu::draw(){
  for(int i = 0; i < MAX_NUMBER_IN_MENU; i+=1)
  {
    this->window.draw(this->menu[i]);
  }

}

MainMenu::~MainMenu(){

}
