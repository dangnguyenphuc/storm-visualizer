#ifndef MAIN_MENU_H
#define MAIN_MENU_H

#pragma once

#include <SFML/Graphics.hpp>

#include "GlobalParameter.hpp"

#define MAX_NUMBER_IN_MENU 3
#define MENU_WIDTH WIN_WIDTH
#define MENU_HEIGHT 12
#define CHARACTER_SIZE MENU_HEIGHT

#define TEXT_COLOR sf::Color::White
#define TEXT_COLOR_HOVER sf::Color::Red
#define MENU_DEFAULT_FONT_PATH "assets/font/JetBrainsMonoNerdFontMono-Regular.ttf"

#define SPACING 20 // in pixels

enum MenuItem{
  PLAY=0,
  OPTIONS,
  EXIT
};


class MainMenu
{
  
  private:
    bool isChoosing;
    sf::RenderWindow& window;
    sf::Font font;
    sf::Text menu[MAX_NUMBER_IN_MENU];
    int selectedItem; 

  public:
    MainMenu(sf::RenderWindow& window);
    ~MainMenu();
    
    void setIsChoosing(bool value);
    
    bool getIsChoosing(){
      return this->isChoosing;
    }
    int getSelectedItem(){
      return this->selectedItem;
    };
    void setSelectedItem(int item);
    void deselectAll();
    void draw();
    void moveRight();
    void moveLeft();
};


#endif
