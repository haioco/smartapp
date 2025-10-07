"""
Bucket Browser Dialog for Haio Smart Storage
Browse bucket contents and share files with temporary URLs
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QMenu, QLineEdit, QProgressBar, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QCursor, QIcon
from share_dialog import ShareDialog, BulkShareDialog


class ObjectListLoader(QThread):
    """Background thread for loading object list."""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, api_client, bucket_name):
        super().__init__()
        self.api_client = api_client
        self.bucket_name = bucket_name
    
    def run(self):
        """Load objects from bucket."""
        try:
            objects = self.api_client.list_objects(self.bucket_name)
            self.finished.emit(objects)
        except Exception as e:
            self.error.emit(str(e))


class BucketBrowserDialog(QDialog):
    """Dialog for browsing bucket contents and sharing files."""
    
    def __init__(self, bucket_name, api_client, parent=None):
        super().__init__(parent)
        self.bucket_name = bucket_name
        self.api_client = api_client
        self.objects = []
        self.current_path = ""  # Current folder path
        self.all_objects = []   # Store all objects for filtering
        
        self.setWindowTitle(f"Browse Bucket: {bucket_name}")
        self.setMinimumSize(900, 600)
        self.setModal(False)  # Allow interaction with main window
        
        self.setup_ui()
        self.load_objects()
    
    def setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Get theme colors from parent or use default detection
        try:
            from main_new import ThemeManager
            theme = ThemeManager()
            colors = theme.get_colors()
        except:
            # Fallback colors
            colors = {
                'bg': '#ffffff',
                'text': '#2c3e50',
                'text_secondary': '#7f8c8d',
                'border': '#e0e0e0',
                'bg_widget': '#ffffff',
                'primary': '#3498db'
            }
        
        # Set dialog background
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['bg']};
            }}
            QLabel {{
                color: {colors['text']};
            }}
        """)
        
        # Header with breadcrumb navigation
        header_layout = QHBoxLayout()
        
        # Up/Back button
        self.up_btn = QPushButton("⬆ Up")
        self.up_btn.setFixedSize(80, 40)
        self.up_btn.clicked.connect(self.go_up)
        self.up_btn.setEnabled(False)
        self.up_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['bg_widget']};
                color: {colors['text']};
                border: 2px solid {colors['border']};
                border-radius: 8px;
                padding: 8px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover:enabled {{
                background-color: {colors['primary']};
                color: white;
                border-color: {colors['primary']};
            }}
            QPushButton:disabled {{
                color: {colors['text_secondary']};
                background-color: {colors['bg']};
            }}
        """)
        header_layout.addWidget(self.up_btn)
        
        # Breadcrumb path
        self.path_label = QLabel(f"[Bucket] {self.bucket_name}")
        self.path_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.path_label.setStyleSheet(f"color: {colors['text']}; padding: 5px;")
        header_layout.addWidget(self.path_label)
        
        header_layout.addStretch()
        
        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Search files...")
        self.search_box.setFixedHeight(40)
        self.search_box.setMinimumWidth(280)
        self.search_box.textChanged.connect(self.filter_objects)
        self.search_box.setStyleSheet(f"""
            QLineEdit {{
                border: 2px solid {colors['border']};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
                background-color: {colors['bg_widget']};
                color: {colors['text']};
            }}
            QLineEdit:focus {{
                border-color: {colors['primary']};
                border-width: 2px;
            }}
        """)
        header_layout.addWidget(self.search_box)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setFixedSize(100, 40)
        refresh_btn.clicked.connect(self.load_objects)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 15px;
                font-weight: bold;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: #2980b9;
            }}
        """)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Loading indicator
        self.loading_bar = QProgressBar()
        self.loading_bar.setRange(0, 0)  # Indeterminate
        self.loading_bar.setTextVisible(False)
        self.loading_bar.setMaximumHeight(3)
        self.loading_bar.hide()
        layout.addWidget(self.loading_bar)
        
        # Objects table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Name", "Size", "Last Modified", "Actions"
        ])
        
        # Configure table
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Set column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        # Enable context menu
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Enable double-click to open folders
        self.table.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        # Style table with improved spacing
        self.table.verticalHeader().setDefaultSectionSize(45)  # Row height
        self.table.setStyleSheet(f"""
            QTableWidget {{
                border: 2px solid {colors['border']};
                border-radius: 8px;
                background-color: {colors['bg_widget']};
                gridline-color: {colors['border']};
                color: {colors['text']};
            }}
            QTableWidget::item {{
                padding: 12px 8px;
                color: {colors['text']};
                border-bottom: 1px solid {colors['border']};
            }}
            QTableWidget::item:selected {{
                background-color: {colors['primary']};
                color: white;
            }}
            QHeaderView::section {{
                background-color: {colors['primary']};
                color: white;
                padding: 12px 10px;
                border: none;
                font-weight: bold;
                font-size: 13px;
            }}
        """)
        
        layout.addWidget(self.table)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"""
            color: {colors['text_secondary']}; 
            font-size: 12px; 
            padding: 8px; 
            background-color: {colors['bg']};
            border-radius: 4px;
        """)
        layout.addWidget(self.status_label)
        
        # Store colors for later use
        self.colors = colors
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        # Share selected button
        self.share_selected_btn = QPushButton("📤 Share Selected")
        self.share_selected_btn.setFixedHeight(45)
        self.share_selected_btn.clicked.connect(self.share_selected)
        self.share_selected_btn.setEnabled(False)
        self.share_selected_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover:enabled {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
                color: #ecf0f1;
            }
        """)
        button_layout.addWidget(self.share_selected_btn)
        
        button_layout.addStretch()
        
        # Close button
        close_btn = QPushButton("✖ Close")
        close_btn.setFixedHeight(45)
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 24px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # Connect selection change
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
    
    def load_objects(self):
        """Load objects from bucket."""
        self.loading_bar.show()
        self.status_label.setText("Loading objects...")
        self.table.setRowCount(0)
        
        # Load in background thread
        self.loader = ObjectListLoader(self.api_client, self.bucket_name)
        self.loader.finished.connect(self.on_objects_loaded)
        self.loader.error.connect(self.on_load_error)
        self.loader.start()
    
    def on_objects_loaded(self, objects):
        """Handle objects loaded successfully."""
        self.loading_bar.hide()
        self.all_objects = objects  # Store all objects
        self.show_current_path()  # Display current folder contents
    
    def on_load_error(self, error_msg):
        """Handle loading error."""
        self.loading_bar.hide()
        self.status_label.setText("Error loading objects")
        QMessageBox.critical(
            self,
            "Error",
            f"Failed to load bucket contents:\n{error_msg}"
        )
    
    def show_current_path(self):
        """Display contents of current path."""
        # Get objects in current folder
        current_items = self.get_current_folder_items()
        
        # Update breadcrumb
        if self.current_path:
            self.path_label.setText(f"[Bucket] {self.bucket_name} / {self.current_path}")
            self.up_btn.setEnabled(True)
        else:
            self.path_label.setText(f"[Bucket] {self.bucket_name}")
            self.up_btn.setEnabled(False)
        
        # Populate table
        self.populate_table(current_items)
        
        # Update status
        folders = len([item for item in current_items if item.get('is_folder')])
        files = len(current_items) - folders
        
        status_parts = []
        if folders > 0:
            status_parts.append(f"{folders} folder{'s' if folders != 1 else ''}")
        if files > 0:
            status_parts.append(f"{files} file{'s' if files != 1 else ''}")
        
        if status_parts:
            total_size = sum(item.get('bytes', 0) for item in current_items if not item.get('is_folder'))
            self.status_label.setText(f"{', '.join(status_parts)} ({self.format_size(total_size)})")
        else:
            self.status_label.setText("Empty folder")
    
    def get_current_folder_items(self):
        """Get items in the current folder (folders and files at this level only)."""
        items = []
        seen_folders = set()
        
        prefix = self.current_path
        prefix_len = len(prefix)
        
        for obj in self.all_objects:
            name = obj.get('name', '')
            
            # Skip if not in current path
            if prefix and not name.startswith(prefix):
                continue
            
            # Get relative path from current folder
            relative_path = name[prefix_len:] if prefix else name
            
            # Check if it's in a subfolder
            if '/' in relative_path:
                # It's in a subfolder - show only the folder
                folder_name = relative_path.split('/')[0]
                
                if folder_name not in seen_folders:
                    seen_folders.add(folder_name)
                    items.append({
                        'name': folder_name,
                        'full_path': prefix + folder_name + '/',
                        'is_folder': True,
                        'bytes': 0,
                        'last_modified': '-'
                    })
            else:
                # It's a file in current folder
                if relative_path:  # Not empty (skip the folder itself)
                    items.append({
                        'name': relative_path,
                        'full_path': name,
                        'is_folder': False,
                        'bytes': obj.get('bytes', 0),
                        'last_modified': obj.get('last_modified', 'Unknown')
                    })
        
        # Sort: folders first, then files, both alphabetically
        items.sort(key=lambda x: (not x.get('is_folder', False), x['name'].lower()))
        
        return items
    
    def populate_table(self, items):
        """Populate table with items (folders and files)."""
        self.table.setRowCount(len(items))
        
        for row, item in enumerate(items):
            is_folder = item.get('is_folder', False)
            name = item.get('name', '')
            
            # Name with folder icon
            if is_folder:
                name_text = f"[Folder] {name}"
                name_item = QTableWidgetItem(name_text)
                name_item.setData(Qt.ItemDataRole.UserRole, item.get('full_path'))
                name_item.setData(Qt.ItemDataRole.UserRole + 1, True)  # is_folder flag
                # Make folder text bold
                font = name_item.font()
                font.setBold(True)
                name_item.setFont(font)
            else:
                name_item = QTableWidgetItem(name)
                name_item.setData(Qt.ItemDataRole.UserRole, item.get('full_path'))
                name_item.setData(Qt.ItemDataRole.UserRole + 1, False)  # is_folder flag
            
            self.table.setItem(row, 0, name_item)
            
            # Size
            if is_folder:
                size_item = QTableWidgetItem("-")
            else:
                size = item.get('bytes', 0)
                size_item = QTableWidgetItem(self.format_size(size))
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 1, size_item)
            
            # Last Modified
            last_modified = item.get('last_modified', 'Unknown')
            time_item = QTableWidgetItem(last_modified)
            self.table.setItem(row, 2, time_item)
            
            # Actions button (for both files and folders)
            if not is_folder:
                # Share button for files
                share_btn = QPushButton("📤 Share")
                share_btn.setFixedSize(85, 32)
                share_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #3498db;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 6px 10px;
                        font-weight: bold;
                        font-size: 11px;
                    }
                    QPushButton:hover {
                        background-color: #2980b9;
                    }
                """)
                share_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                share_btn.clicked.connect(
                    lambda checked, full_path=item.get('full_path'): self.share_single(full_path)
                )
                self.table.setCellWidget(row, 3, share_btn)
            else:
                # Share folder button
                share_folder_btn = QPushButton("📁 Share All")
                share_folder_btn.setFixedSize(95, 32)
                share_folder_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #27ae60;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 6px 10px;
                        font-weight: bold;
                        font-size: 10px;
                    }
                    QPushButton:hover {
                        background-color: #229954;
                    }
                """)
                share_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                share_folder_btn.clicked.connect(
                    lambda checked, full_path=item.get('full_path'): self.share_folder(full_path)
                )
                self.table.setCellWidget(row, 3, share_folder_btn)
    
    def on_item_double_clicked(self, item):
        """Handle double-click on item - navigate into folders."""
        row = item.row()
        name_item = self.table.item(row, 0)
        
        if name_item:
            is_folder = name_item.data(Qt.ItemDataRole.UserRole + 1)
            
            if is_folder:
                # Navigate into folder
                full_path = name_item.data(Qt.ItemDataRole.UserRole)
                self.current_path = full_path
                self.show_current_path()
                self.search_box.clear()  # Clear search when navigating
    
    def go_up(self):
        """Navigate up one folder level."""
        if not self.current_path:
            return
        
        # Remove trailing slash
        path = self.current_path.rstrip('/')
        
        # Go up one level
        if '/' in path:
            self.current_path = path.rsplit('/', 1)[0] + '/'
        else:
            self.current_path = ""
        
        self.show_current_path()
        self.search_box.clear()  # Clear search when navigating
    
    def filter_objects(self, text):
        """Filter objects by search text."""
        text = text.lower()
        
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 0)
            if name_item:
                should_show = text in name_item.text().lower()
                self.table.setRowHidden(row, not should_show)
    
    def on_selection_changed(self):
        """Handle selection change."""
        selected_rows = len(self.table.selectionModel().selectedRows())
        self.share_selected_btn.setEnabled(selected_rows > 0)
        
        if selected_rows > 0:
            self.share_selected_btn.setText(
                f"📤 Share Selected ({selected_rows})"
            )
        else:
            self.share_selected_btn.setText("📤 Share Selected")
    
    def get_selected_objects(self):
        """Get list of selected object full paths (files only, no folders)."""
        selected_rows = self.table.selectionModel().selectedRows()
        object_names = []
        
        for index in selected_rows:
            row = index.row()
            name_item = self.table.item(row, 0)
            if name_item:
                is_folder = name_item.data(Qt.ItemDataRole.UserRole + 1)
                if not is_folder:  # Only include files
                    full_path = name_item.data(Qt.ItemDataRole.UserRole)
                    object_names.append(full_path)
        
        return object_names
    
    def share_single(self, object_name):
        """Share a single object."""
        dialog = ShareDialog(
            object_name,
            self.bucket_name,
            self.api_client,
            self
        )
        dialog.exec()
    
    def share_selected(self):
        """Share selected objects."""
        selected = self.get_selected_objects()
        
        if not selected:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select one or more files to share."
            )
            return
        
        if len(selected) == 1:
            # Single file - use standard share dialog
            self.share_single(selected[0])
        else:
            # Multiple files - use bulk share dialog
            dialog = BulkShareDialog(
                selected,
                self.bucket_name,
                self.api_client,
                self
            )
            dialog.exec()
    
    def show_context_menu(self, position):
        """Show context menu for table items."""
        # Get the item under cursor
        item = self.table.itemAt(position)
        if not item:
            return
        
        row = item.row()
        name_item = self.table.item(row, 0)
        if not name_item:
            return
        
        is_folder = name_item.data(Qt.ItemDataRole.UserRole + 1)
        full_path = name_item.data(Qt.ItemDataRole.UserRole)
        display_name = name_item.text()
        
        # Create context menu
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {self.colors['bg_widget']};
                border: 1px solid {self.colors['border']};
                border-radius: 4px;
                color: {self.colors['text']};
            }}
            QMenu::item {{
                padding: 8px 20px;
            }}
            QMenu::item:selected {{
                background-color: {self.colors['primary']};
                color: white;
            }}
        """)
        
        # Add actions based on type
        if is_folder:
            open_action = menu.addAction("Open folder")
            menu.addSeparator()
            share_folder_action = menu.addAction("Share all files in folder")
            copy_name_action = menu.addAction("Copy folder name")
        else:
            share_action = menu.addAction("Share this file")
            copy_name_action = menu.addAction("Copy filename")
            
            menu.addSeparator()
            
            share_all_action = menu.addAction("Share all selected files")
        
        # Execute menu and handle action
        action = menu.exec(QCursor.pos())
        
        if is_folder:
            if action == open_action:
                self.current_path = full_path
                self.show_current_path()
                self.search_box.clear()
            elif action == share_folder_action:
                self.share_folder(full_path)
            elif action == copy_name_action:
                clipboard = QApplication.clipboard()
                clipboard.setText(display_name.replace("[Folder] ", ""))
                self.status_label.setText(f"Copied: {display_name}")
        else:
            if action == share_action:
                self.share_single(full_path)
            elif action == copy_name_action:
                clipboard = QApplication.clipboard()
                clipboard.setText(display_name)
                self.status_label.setText(f"Copied: {display_name}")
            elif action == share_all_action:
                self.share_selected()
    
    def share_folder(self, folder_path):
        """Share all files in a folder."""
        # Get all files in this folder (recursively)
        files_in_folder = []
        
        for obj in self.all_objects:
            obj_name = obj.get('name', '')
            # Check if file is in this folder
            if obj_name.startswith(folder_path):
                # It's a file, not a subfolder marker
                if not obj_name.endswith('/'):
                    files_in_folder.append(obj_name)
        
        if not files_in_folder:
            QMessageBox.information(
                self,
                "Empty Folder",
                f"No files found in this folder."
            )
            return
        
        # Show folder name without path
        folder_name = folder_path.rstrip('/').split('/')[-1] if '/' in folder_path else folder_path.rstrip('/')
        
        # Confirm with user
        reply = QMessageBox.question(
            self,
            "Share Folder",
            f"Share all {len(files_in_folder)} file(s) in folder '{folder_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Use bulk share dialog
            dialog = BulkShareDialog(
                files_in_folder,
                self.bucket_name,
                self.api_client,
                self
            )
            dialog.exec()
    
    def format_size(self, bytes_size: int) -> str:
        """Format bytes to human readable size."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} PB"
