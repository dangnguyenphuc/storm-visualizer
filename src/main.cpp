#include <SFML/Graphics.hpp>
#include "../include/MainMenu.hpp"
#include "../include/GlobalParameter.hpp"


int main()
{
    sf::RenderWindow window(sf::VideoMode(WIN_WIDTH, WIN_HEIGHT), TITLE);  

    sf::Font font;
    if(!font.loadFromFile(FONT_PATH))
    {
      printf("%s", "\nERROR: Cannot load font!");
      return -1;
    }

    
    MainMenu menu(window);
    bool menuToggle = false;

    // --------- DEBUG --
    // sf::Text text;
    // text.setFont(font);
    // text.setCharacterSize(24);
    // text.setString("Hello");
    // text.setFillColor(sf::Color::Green);
    // text.setPosition(400,300);
    // ------------------


    while (window.isOpen())
    {
      sf::Event event;
      while (window.pollEvent(event))
      {
        switch (event.type) 
        {

          case sf::Event::KeyReleased :
            switch (event.key.code) {
              
              case sf::Keyboard::Escape :
                menuToggle = !menuToggle;
                menu.setIsChoosing(menuToggle);
                break;

              case sf::Keyboard::Right :
                menu.moveRight();
                break;
              
              case sf::Keyboard::Left :
                menu.moveLeft();
                break;
              
              case sf::Keyboard::Return : 
                if(menuToggle){
                  switch (menu.getSelectedItem()) {
                    case PLAY:
                      printf("You Press PLAY\n"); 
                      break;
                    case OPTIONS:
                      printf("You Press OPTS\n");
                      break;
                    case EXIT:
                      printf("You Press EXIT\n");
                      window.close();
                      break;
                    default:
                      break;
                  }
                } 
                break;

              default:
                break;
            }

            break;
          
          case sf::Event::Closed :
            window.close();
            break;
          
          default: 
            break;
        
        }
      
      }
  
      window.clear();
      menu.draw();

      //window.draw(text);

      window.display();
     }    

}
