CC := g++
CFLAGS := -std=c++11 -Wall -Wextra
SFMLFLAGS := -lsfml-graphics -lsfml-window -lsfml-system

SRC_DIR := src
OBJ_DIR := obj
BIN_DIR := bin
INCLUDE_DIR := include

SRC_FILES := $(wildcard $(SRC_DIR)/*.cpp)
OBJ_FILES := $(patsubst $(SRC_DIR)/%.cpp, $(OBJ_DIR)/%.o, $(SRC_FILES))

EXECUTABLE := $(BIN_DIR)/program.bin

all: $(EXECUTABLE)

$(EXECUTABLE): $(OBJ_FILES)
	@mkdir -p $(BIN_DIR)
	$(CC) $(CFLAGS) -I$(INCLUDE_DIR) $^ -o $@ $(SFMLFLAGS)

$(OBJ_DIR)/%.o: $(SRC_DIR)/%.cpp
	@mkdir -p $(OBJ_DIR)
	$(CC) $(CFLAGS) -I$(INCLUDE_DIR) -c $< -o $@

clean:
	rm -rf $(OBJ_DIR) $(BIN_DIR)

.PHONY: all clean

