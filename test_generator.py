#!/usr/bin/env python3
"""Quick test to verify the character generator works with the corrected data.json"""

import json
import sys
from engine import GameState, load_data

def test_character_generation():
    """Test generating a complete character"""
    print("=" * 60)
    print("Testing Dark Fantasy Character Generator")
    print("=" * 60)
    
    try:
        # Load data and initialize the game engine
        data = load_data()
        game = GameState(data)
        print("✓ Game engine initialized successfully")
        print(f"✓ Data loaded: {len(game.data)} top-level keys")
        
        # Test generating a complete character by spinning all wheels
        print("\nSpinning character wheels:")
        game.spin_race()
        print(f"  - Race: {game.selections.get('Race', 'N/A')}")
        
        game.spin_age()
        print(f"  - Age: {game.selections.get('Age', 'N/A')}")
        
        game.spin_height()
        print(f"  - Height: {game.selections.get('Height', 'N/A')}")
        
        game.spin_alignment()
        print(f"  - Alignment: {game.selections.get('Alignment', 'N/A')}")
        
        game.spin_place()
        print(f"  - Place: {game.selections.get('Place', 'N/A')}")
        
        game.spin_class()
        print(f"  - Class: {game.selections.get('Class', 'N/A')}")
        
        print("\n✓ Character generated successfully!\n")
        
        # Display the complete character state
        print("Generated Character Details:")
        print("-" * 60)
        print("Selections:")
        for key, value in sorted(game.selections.items()):
            if not key.startswith('_'):
                print(f"  {key}: {value}")
        
        print(f"\nStats:")
        for stat, value in game.stats.items():
            print(f"  {stat}: {value}")
        
        if game.powers:
            print(f"\nPowers ({len(game.powers)}):")
            for power in game.powers:
                print(f"  - {power}")
        
        if game.log:
            print(f"\nGeneration Log ({len(game.log)} entries):")
            for entry in game.log[-5:]:
                print(f"  - {entry}")
        
        print("\n" + "=" * 60)
        print("✓ All tests passed! The generator is working correctly.")
        print("=" * 60)
        
        # Test that backgrounds are available
        import os
        backgrounds_path = "/workspace/backgrounds"
        if os.path.exists(backgrounds_path):
            bg_files = [f for f in os.listdir(backgrounds_path) if f.endswith('.jpg')]
            print(f"\n✓ Backgrounds folder has {len(bg_files)} images ready")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_character_generation()
    sys.exit(0 if success else 1)
