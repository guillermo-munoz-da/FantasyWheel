# Dark Fantasy Character Generator - UI Redesign

## New Interface Features

### 1. **Black Background**
- The application starts with a completely **black background** (#000000)
- Clean, dark aesthetic that emphasizes the spinning wheels

### 2. **Dynamic Background Images**
- When you spin the **Place wheel** and select a location, the black background automatically changes to the corresponding place image
- Supported backgrounds:
  - **Dwarven Hold** - Stone halls and forges
  - **Elven Forest** - Magical woods and ancient trees
  - **Human City** - Urban settlements with good factions
  - **Human Slums** - Dark city underbelly
  - **Outlands** - Wild, untamed wilderness

### 3. **Spinning Wheels - One at a Time**
- Each wheel is displayed **individually and centered** on the canvas
- Much larger display for better visibility
- Grid layout of color-coded options
- Current wheel label shows which wheel you're spinning

### 4. **Spin Button**
- Large, prominent **GIRAR (SPIN) button** in the bottom right
- Easy to find and click
- Disables when all wheels have been spun

### 5. **Wheel Order**
The character generation follows this sequence:
1. **Race** - Select your character's race
2. **Archetype** - Choose your archetype
3. **Alignment** - Pick your moral alignment
4. **Place** - Select your origin place (triggers background image)
5. **Magic Type** - Choose your magic type
6. **Event** - Select a defining event
7. **Personality** - Pick personality traits

### 6. **Visual Feedback**
- Selected/highlighted options have **golden highlighting**
- Each option has a unique color for visual distinction
- Smooth animation during spinning
- Ease-out effect for realistic spinning

### 7. **Selection Tracking**
- Top-right panel shows all selected values so far
- Updates in real-time as you spin each wheel
- Color-coded display for easy reading

## How to Use

1. **Start the app**: `python main_tk.py`
2. **Initial state**: Black background with the Race wheel displayed
3. **Click GIRAR**: The wheel spins and randomly selects an option
4. **View result**: Selection updates in the selection panel
5. **Background changes**: When you spin the Place wheel, the background image updates
6. **Continue**: Move through all wheels until complete
7. **Done**: When all wheels are spun, you'll see "¡Generación Completada!"

## Technical Details

- **Resolution**: 1200x800 pixels
- **Colors**:
  - Primary background: #000000 (Black)
  - Accent color: #eebc1d (Gold)
  - Wheel container: #1a1a2e (Dark blue-black)
  - Selection panel: #1a1a2e (Dark blue-black)

- **Background Images**: Located in `/workspace/backgrounds/`
- **Supported formats**: JPG
- **Image size**: Scaled to 1200x800 for full window coverage

## File Locations

- Main UI: `/workspace/main_tk.py`
- Character engine: `/workspace/engine.py`
- Configuration: `/workspace/data.json`
- Backgrounds: `/workspace/backgrounds/`
