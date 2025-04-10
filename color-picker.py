import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog
import pyautogui
import keyboard  # This is the keyboard module for global hotkeys
import pyperclip
import os
import json
import shutil
from pynput import mouse
from pynput.keyboard import Key, Listener as KeyboardListener  # This is the pynput keyboard listener

def get_data_directory():
    """Get the directory to store application data."""
    # Check for a config file first
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                if 'data_dir' in config and os.path.exists(config['data_dir']):
                    return config['data_dir']
        except Exception as e:
            print(f"Error reading config: {e}")

    # Use AppData on Windows as fallback
    appdata = os.getenv('APPDATA')
    if appdata:
        data_dir = os.path.join(appdata, "ColorPickerTool")
    else:
        # Fallback to user's home directory
        data_dir = os.path.join(os.path.expanduser("~"), ".colorpickertool")

    # Create directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

class ColorPickerApp:
    def __init__(self, root):
        # Set up the main window
        self.root = root
        self.root.title("Color Picker Tool")
        self.root.geometry("900x400")  # Larger window to accommodate favorites
        self.root.resizable(False, False)

        # Create a string variable for status
        self.status_var = tk.StringVar(value="Ready")

        # Favorites storage
        self.favorites = []
        self.load_favorites()  # Load favorites from file if exists

        # Try to set icon only if file exists
        icon_path = 'color_picker.ico'
        if os.path.exists(icon_path) and hasattr(root, 'iconbitmap'):
            try:
                self.root.iconbitmap(default=icon_path)
            except tk.TclError:
                # If icon loading fails, continue without the icon
                pass

        # Add settings option to menu
        menubar = tk.Menu(root)
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="Set Favorites Directory", command=self.set_data_directory)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        root.config(menu=menubar)

        # Create style
        style = ttk.Style()
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TButton", font=("Arial", 12))
        style.configure("TLabel", font=("Arial", 12), background="#f0f0f0")

        # Create custom styles for centered text
        style.configure("Center.TLabel", anchor="center", justify="center")

        # Make sure the left and right frames have proper width
        root.update_idletasks()  # Update to get proper dimensions

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
        # Container for title and instructions to ensure centering
        title_container = tk.Frame(self.left_frame, bg="#f0f0f0")
        title_container.pack(fill=tk.X)

        # Title label - using tk.Label for better centering control
        self.title_label = tk.Label(title_container, text="Screen Color Picker",
                                     font=("Arial", 16, "bold"), bg="#f0f0f0")
        self.title_label.pack(pady=(0, 15), fill=tk.X)

        # Instructions - Using tk.Label for better centering
        self.instructions = tk.Label(title_container,
                                     text="F2 to activate color picker.\nPosition cursor and press SHIFT to select color.",
                                     font=("Arial", 12), bg="#f0f0f0")
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
        status_container = tk.Frame(self.left_frame, bg="#f0f0f0")
        status_container.pack(pady=(10, 0), fill=tk.X)

        self.status_label = tk.Label(status_container, textvariable=self.status_var,
                                     font=("Arial", 10), foreground="gray", bg="#f0f0f0")
        self.status_label.pack(fill=tk.X)

        # ----- RIGHT PANEL - FAVORITES -----
        # Container for favorites title and instructions to ensure centering
        fav_title_container = tk.Frame(self.right_frame, bg="#f0f0f0")
        fav_title_container.pack(fill=tk.X)

        # Title for favorites - using tk.Label for better centering
        self.favorites_title = tk.Label(fav_title_container, text="Favorite Colors",
                                         font=("Arial", 16, "bold"), bg="#f0f0f0")
        self.favorites_title.pack(pady=(0, 15), fill=tk.X)

        # Favorites instructions - using tk.Label for better centering
        self.favorites_instructions = tk.Label(fav_title_container,
                                              text="Double click a saved color to load into picker.",
                                              font=("Arial", 12), bg="#f0f0f0")
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

        # Configure column headings with center alignment
        self.favorites_list.heading("Label", text="Label", anchor="center")
        self.favorites_list.heading("Hex", text="Hex Code", anchor="center")

        # Configure columns with center alignment and appropriate width
        self.favorites_list.column("Label", width=120, anchor="center")
        self.favorites_list.column("Hex", width=100, anchor="center")

        self.favorites_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.favorites_list.yview)

        # Configure row height to allow for text wrapping
        self.favorites_list.configure(height=10)  # Adjust visible rows

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

    def set_data_directory(self):
        """Allow user to set custom data directory"""
        # Get initial directory
        current_dir = get_data_directory()

        # Ask user to select a directory
        new_dir = filedialog.askdirectory(
            title="Select Data Directory",
            initialdir=current_dir
        )

        # If user canceled, return
        if not new_dir:
            return

        # Confirm with user
        if messagebox.askyesno(
            "Confirm Directory Change",
            f"Set data directory to:\n{new_dir}\n\nExisting favorites will be moved to the new location."
        ):
            try:
                # Create config file
                config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
                config = {'data_dir': new_dir}

                # Create the new directory if it doesn't exist
                os.makedirs(new_dir, exist_ok=True)

                # Save config
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=2)

                # Try to move existing favorites if they exist
                old_favorites = os.path.join(current_dir, 'favorites.json')
                new_favorites = os.path.join(new_dir, 'favorites.json')

                if os.path.exists(old_favorites) and old_favorites != new_favorites:
                    shutil.copy2(old_favorites, new_favorites)

                # Reload favorites from new location
                self.load_favorites()

                # Update status
                self.status_var.set(f"Data directory changed to {new_dir}")

            except Exception as e:
                messagebox.showerror("Error", f"Could not set data directory: {e}")
                return

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
        # Show a message that color picker is active
        self.status_var.set("Color picker activated - press SHIFT to pick a color without clicking")

        # Disable the F2 hotkey temporarily to avoid multiple activations
        keyboard.unhook_all()

        # Create a small preview window that will follow the cursor
        preview = tk.Toplevel(self.root)
        preview.overrideredirect(True)  # Remove window decorations
        preview.attributes('-topmost', True)  # Keep on top of other windows

        # Create a frame to show the color
        color_preview = tk.Frame(preview, width=60, height=30, bg="#FFFFFF")
        color_preview.pack(side=tk.TOP, pady=2, padx=2)

        # Label to show hex code
        hex_label = tk.Label(preview, text="#FFFFFF", bg="#F0F0F0", font=("Arial", 9))
        hex_label.pack(side=tk.BOTTOM, pady=2, padx=2, fill=tk.X)

        # Position window near cursor but not directly under it
        preview.geometry(f"80x50+{pyautogui.position()[0]+20}+{pyautogui.position()[1]-60}")

        # This flag tracks if we're exiting the listener
        self.picking_active = True

        # Function to handle key press
        def on_key_release(key):
            try:
                # Check if shift was pressed
                if key == Key.shift and self.picking_active:
                    self.picking_active = False

                    # Get the current mouse position
                    x, y = pyautogui.position()

                    # Get the pixel color at position
                    pixel_color = pyautogui.screenshot().getpixel((x, y))

                    # Convert RGB to hex
                    hex_color = '#{:02x}{:02x}{:02x}'.format(pixel_color[0], pixel_color[1], pixel_color[2])

                    # Update the UI (need to schedule this for when window returns)
                    def update_ui():
                        self.color_frame.config(bg=hex_color)
                        self.hex_var.set(hex_color.upper())
                        self.status_var.set(f"Picked color at ({x}, {y})")
                        # Re-register the F2 hotkey
                        keyboard.add_hotkey('f2', self.pick_color)
                        # Destroy the preview window
                        preview.destroy()

                    # Restore the window, bring to foreground, and update UI
                    def restore_window():
                        self.root.deiconify()
                        self.root.lift()
                        self.root.focus_force()  # Force focus to the window
                        self.root.attributes('-topmost', True)  # Place window on top
                        self.root.update()
                        self.root.attributes('-topmost', False)  # Allow window to go behind others when user clicks elsewhere

                    self.root.after(100, restore_window)
                    self.root.after(200, update_ui)

                    # Stop listening
                    return False
            except AttributeError:
                # Handle case where key doesn't have the expected attributes
                pass

            # Check for Escape key to cancel
            if key == Key.esc and self.picking_active:
                self.picking_active = False
                preview.destroy()

                def restore_on_cancel():
                    self.root.deiconify()
                    self.status_var.set("Color picking cancelled")
                    # Re-register the F2 hotkey
                    keyboard.add_hotkey('f2', self.pick_color)

                self.root.after(100, restore_on_cancel)
                return False

            return True

        # Also handle mouse movement to show color preview in status bar
        def on_mouse_move(x, y):
            if not self.picking_active:
                return False

            try:
                # Move the preview window to follow cursor
                preview.geometry(f"80x50+{x+20}+{y-60}")

                # Get color under cursor
                pixel_color = pyautogui.screenshot().getpixel((x, y))
                hex_color = '#{:02x}{:02x}{:02x}'.format(pixel_color[0], pixel_color[1], pixel_color[2])

                # Update preview
                color_preview.config(bg=hex_color)
                hex_label.config(text=hex_color.upper())
            except:
                pass
            return True

        # Start listeners
        key_listener = KeyboardListener(on_release=on_key_release)
        key_listener.start()

        mouse_listener = mouse.Listener(on_move=on_mouse_move)
        mouse_listener.start()

        # Minimize the main window
        self.root.iconify()

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
        # Get data directory for storing favorites
        data_dir = get_data_directory()
        favorites_file = os.path.join(data_dir, 'favorites.json')

        # Check if file exists
        if os.path.exists(favorites_file):
            try:
                with open(favorites_file, 'r') as f:
                    self.favorites = json.load(f)
                self.status_var.set(f"Loaded favorites from {favorites_file}")
            except Exception as e:
                print(f"Error loading favorites: {e}")
                self.favorites = []
        else:
            self.favorites = []
            print(f"No favorites file found at {favorites_file}")

    def save_favorites(self):
        # Get data directory for storing favorites
        data_dir = get_data_directory()
        favorites_file = os.path.join(data_dir, 'favorites.json')

        # Save to file
        try:
            with open(favorites_file, 'w') as f:
                json.dump(self.favorites, f, indent=2)
            # Show save location in status
            self.status_var.set(f"Saved favorites to {favorites_file}")
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

            # Insert with wrapped text
            self.favorites_list.insert("", "end", values=(favorite["label"], hex_code),
                                     tags=(tag_name,))

            # Configure the tag with appropriate background and foreground colors
            text_color = "white" if is_dark else "black"
            self.favorites_list.tag_configure(tag_name, background=hex_code, foreground=text_color)

        # Set row height to accommodate wrapped text - using style instead of direct configuration
        style = ttk.Style()
        style.configure('Treeview', rowheight=40)

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