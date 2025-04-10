import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import pyautogui
import keyboard
import pyperclip
import os
import json
import colorsys

class ColorPickerApp:
    def __init__(self, root):
        # Set up the main window
        self.root = root
        self.root.title("Color Picker Tool")
        self.root.geometry("625x400")  # Larger window to accommodate favorites
        self.root.resizable(False, False)

        # Favorites storage
        self.favorites = []
        self.load_favorites()  # Load favorites from file if exists

        # Try to set icon only if file exists
        icon_path = r'I:\My Drive\_00_GitHub\Color-Picker-Tool\assets\dropper.ico'
        if os.path.exists(icon_path) and hasattr(root, 'iconbitmap'):
            try:
                self.root.iconbitmap(default=icon_path)
            except tk.TclError:
                # If icon loading fails, continue without the icon
                pass

        # Create style
        style = ttk.Style()
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TButton", font=("Arial", 12))
        style.configure("TLabel", font=("Arial", 12), background="#f0f0f0")

        # Main container with left and right panels
        self.container = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.container.pack(fill=tk.BOTH, expand=True)

        # Left panel - Color Picker
        self.left_frame = ttk.Frame(self.container, padding="20 20 20 20", style="TFrame")

        # Right panel - Favorites
        self.right_frame = ttk.Frame(self.container, padding="20 20 20 20", style="TFrame")

        # Add frames to paned window
        self.container.add(self.left_frame, weight=1)
        self.container.add(self.right_frame, weight=1)

        # ----- LEFT PANEL - COLOR PICKER -----
        # Title label
        self.title_label = ttk.Label(self.left_frame, text="Screen Color Picker",
                                     font=("Arial", 16, "bold"), style="TLabel")
        self.title_label.pack(pady=(0, 15))

        # Instructions
        self.instructions = ttk.Label(self.left_frame,
                                     text="Mouse over any color.\nF2 to pick a color from screen",
                                     style="TLabel",
                                     justify="center")
        self.instructions.pack(pady=(0, 10), fill=tk.X)

        # Color display
        self.color_frame = tk.Frame(self.left_frame, width=100, height=50, bg="#ffffff")
        self.color_frame.pack(pady=(0, 10))

        # Container frame for hex entry
        self.hex_container = tk.Frame(self.left_frame, bd=2, relief="groove")
        self.hex_container.pack(pady=(0, 10))

        # Hex code display
        self.hex_var = tk.StringVar(value="#FFFFFF")
        self.hex_entry = tk.Entry(self.hex_container, textvariable=self.hex_var,
                                 width=10, font=("Arial", 12), justify="center",
                                 bd=0, highlightthickness=0)  # Remove border as container has it

        # Fixed padding for the entry field
        self.hex_entry.pack(padx=5, pady=5)

        # Buttons frame
        button_frame = ttk.Frame(self.left_frame)
        button_frame.pack(pady=(0, 10), fill=tk.X)

        # Copy button
        self.copy_button = tk.Button(button_frame, text="Copy Hex",
                                   font=("Arial", 12),
                                   command=self.copy_to_clipboard,
                                   pady=5)  # Fixed padding
        self.copy_button.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)

        # Add to favorites button
        self.fav_button = tk.Button(button_frame, text="Add to Favorites",
                                  font=("Arial", 12),
                                  command=self.add_to_favorites,
                                  pady=5)  # Fixed padding
        self.fav_button.pack(side=tk.RIGHT, padx=(5, 0), fill=tk.X, expand=True)

        # Status indicator
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(self.left_frame, textvariable=self.status_var,
                                     font=("Arial", 10), foreground="gray")
        self.status_label.pack(pady=(10, 0))

        # ----- RIGHT PANEL - FAVORITES -----
        # Title for favorites
        self.favorites_title = ttk.Label(self.right_frame, text="Favorite Colors",
                                         font=("Arial", 16, "bold"), style="TLabel")
        self.favorites_title.pack(pady=(0, 15))

        # Favorites instructions
        self.favorites_instructions = ttk.Label(self.right_frame,
                                      text="Double click a saved color to load to picker",
                                      style="TLabel",
                                      justify="center")
        self.favorites_instructions.pack(pady=(0, 10), fill=tk.X)

        # Frame for favorites list
        self.favorites_frame = ttk.Frame(self.right_frame)
        self.favorites_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollbar for favorites
        self.scrollbar = ttk.Scrollbar(self.favorites_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Favorites listbox with columns
        self.favorites_list = ttk.Treeview(self.favorites_frame,
                                           columns=("Label", "Hex"),
                                           show="headings",
                                           yscrollcommand=self.scrollbar.set)

        self.favorites_list.heading("Label", text="Label")
        self.favorites_list.heading("Hex", text="Hex Code")

        self.favorites_list.column("Label", width=120)
        self.favorites_list.column("Hex", width=100)

        self.favorites_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.favorites_list.yview)

        # Bind double-click to load color
        self.favorites_list.bind("<Double-1>", self.load_selected_color)
        # Bind right-click to show context menu
        self.favorites_list.bind("<Button-3>", self.show_context_menu)

        # Favorites action buttons
        fav_buttons_frame = ttk.Frame(self.right_frame)
        fav_buttons_frame.pack(fill=tk.X, pady=(10, 0))

        # Delete button
        self.delete_button = ttk.Button(fav_buttons_frame, text="Delete Selected",
                                      command=self.delete_favorite)
        self.delete_button.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)

        # Edit button
        self.edit_button = ttk.Button(fav_buttons_frame, text="Edit Label",
                                    command=self.edit_favorite_label)
        self.edit_button.pack(side=tk.RIGHT, padx=(5, 0), fill=tk.X, expand=True)

        # Register the hotkey
        keyboard.add_hotkey('f2', self.pick_color)

        # Populate favorites list
        self.refresh_favorites_list()

    def is_dark_color(self, hex_color):
        """Determine if a color is dark (needing white text) or light (needing black text)"""
        # Remove the # symbol if present
        hex_color = hex_color.lstrip('#')

        # Convert hex to RGB
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0

        # Calculate brightness using perceived luminance formula
        # This formula takes into account human perception of different colors
        brightness = (0.299 * r + 0.587 * g + 0.114 * b)

        # Return True if the color is dark (needing white text)
        return brightness < 0.5

    def pick_color(self):
        # Minimize the window temporarily
        self.root.iconify()
        self.root.after(500)  # Small delay to allow window to minimize

        # Get the mouse position and pixel color
        x, y = pyautogui.position()
        pixel_color = pyautogui.screenshot().getpixel((x, y))

        # Convert RGB to hex
        hex_color = '#{:02x}{:02x}{:02x}'.format(pixel_color[0], pixel_color[1], pixel_color[2])

        # Update the UI
        self.color_frame.config(bg=hex_color)
        self.hex_var.set(hex_color.upper())
        self.status_var.set(f"Picked color at ({x}, {y})")

        # Restore the window
        self.root.after(100, self.root.deiconify)

    def copy_to_clipboard(self):
        # Copy the hex code to clipboard
        hex_code = self.hex_var.get()
        pyperclip.copy(hex_code)
        self.status_var.set(f"Copied {hex_code} to clipboard")

    def add_to_favorites(self):
        # Get the current color
        hex_code = self.hex_var.get()

        # Ask for a label
        label = simpledialog.askstring("Add to Favorites",
                                      "Enter a label for this color:",
                                      parent=self.root)

        # If user canceled, return
        if label is None:
            return

        # Create favorite entry
        favorite = {
            "label": label,
            "hex": hex_code
        }

        # Add to favorites list
        self.favorites.append(favorite)

        # Save favorites
        self.save_favorites()

        # Refresh the displayed list
        self.refresh_favorites_list()

        self.status_var.set(f"Added {hex_code} to favorites as '{label}'")

    def load_favorites(self):
        # Create favorites file path
        favorites_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'favorites.json')

        # Check if file exists
        if os.path.exists(favorites_file):
            try:
                with open(favorites_file, 'r') as f:
                    self.favorites = json.load(f)
            except Exception as e:
                print(f"Error loading favorites: {e}")
                self.favorites = []

    def save_favorites(self):
        # Create favorites file path
        favorites_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'favorites.json')

        # Save to file
        try:
            with open(favorites_file, 'w') as f:
                json.dump(self.favorites, f, indent=2)
        except Exception as e:
            print(f"Error saving favorites: {e}")
            messagebox.showerror("Error", f"Could not save favorites: {e}")

    def refresh_favorites_list(self):
        # Clear current items
        for item in self.favorites_list.get_children():
            self.favorites_list.delete(item)

        # Add favorites to list
        for favorite in self.favorites:
            hex_code = favorite["hex"]
            is_dark = self.is_dark_color(hex_code)

            # Create a unique tag for this item combining color and text color info
            tag_name = f"{hex_code}_{is_dark}"

            self.favorites_list.insert("", "end", values=(favorite["label"], hex_code),
                                     tags=(tag_name,))

            # Configure the tag with appropriate background and foreground colors
            text_color = "white" if is_dark else "black"
            self.favorites_list.tag_configure(tag_name, background=hex_code, foreground=text_color)

    def load_selected_color(self, event):
        # Get selected item
        selected = self.favorites_list.selection()

        if not selected:
            return

        # Get values of selected item
        values = self.favorites_list.item(selected[0], 'values')

        if not values:
            return

        # Extract hex code
        hex_code = values[1]

        # Update UI
        self.color_frame.config(bg=hex_code)
        self.hex_var.set(hex_code)
        self.status_var.set(f"Loaded color {hex_code}")

    def delete_favorite(self):
        # Get selected item
        selected = self.favorites_list.selection()

        if not selected:
            messagebox.showinfo("Info", "Please select a favorite to delete")
            return

        # Get values of selected item
        values = self.favorites_list.item(selected[0], 'values')

        if not values:
            return

        # Ask for confirmation
        if messagebox.askyesno("Confirm", f"Delete '{values[0]}' ({values[1]})?"):
            # Find and remove from favorites
            for i, favorite in enumerate(self.favorites):
                if favorite["label"] == values[0] and favorite["hex"] == values[1]:
                    del self.favorites[i]
                    break

            # Save and refresh
            self.save_favorites()
            self.refresh_favorites_list()
            self.status_var.set(f"Deleted '{values[0]}' from favorites")

    def edit_favorite_label(self):
        # Get selected item
        selected = self.favorites_list.selection()

        if not selected:
            messagebox.showinfo("Info", "Please select a favorite to edit")
            return

        # Get values of selected item
        values = self.favorites_list.item(selected[0], 'values')

        if not values:
            return

        # Ask for new label
        new_label = simpledialog.askstring("Edit Label",
                                         "Enter a new label:",
                                         initialvalue=values[0],
                                         parent=self.root)

        # If user canceled, return
        if new_label is None:
            return

        # Find and update in favorites
        for favorite in self.favorites:
            if favorite["label"] == values[0] and favorite["hex"] == values[1]:
                favorite["label"] = new_label
                break

        # Save and refresh
        self.save_favorites()
        self.refresh_favorites_list()
        self.status_var.set(f"Updated label to '{new_label}'")

    def show_context_menu(self, event):
        # Get selected item
        selected = self.favorites_list.identify_row(event.y)

        if not selected:
            return

        # Select the item under cursor
        self.favorites_list.selection_set(selected)

        # Create context menu
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(label="Copy Hex", command=self.copy_selected_hex)
        context_menu.add_command(label="Load Color", command=lambda: self.load_selected_color(None))
        context_menu.add_separator()
        context_menu.add_command(label="Edit Label", command=self.edit_favorite_label)
        context_menu.add_command(label="Delete", command=self.delete_favorite)

        # Display context menu
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    def copy_selected_hex(self):
        # Get selected item
        selected = self.favorites_list.selection()

        if not selected:
            return

        # Get values of selected item
        values = self.favorites_list.item(selected[0], 'values')

        if not values:
            return

        # Copy hex code to clipboard
        hex_code = values[1]
        pyperclip.copy(hex_code)
        self.status_var.set(f"Copied {hex_code} to clipboard")

def main():
    root = tk.Tk()
    app = ColorPickerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()