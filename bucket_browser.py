"""
Bucket Browser Dialog for Haio Smart Storage
Browse bucket contents and share files with temporary URLs
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QMenu, QLineEdit, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QCursor
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
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel(f"Files in {self.bucket_name}")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {colors['text']};")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search files...")
        self.search_box.setMinimumWidth(250)
        self.search_box.textChanged.connect(self.filter_objects)
        self.search_box.setStyleSheet(f"""
            QLineEdit {{
                border: 2px solid {colors['border']};
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
                background-color: {colors['bg_widget']};
                color: {colors['text']};
            }}
            QLineEdit:focus {{
                border-color: {colors['primary']};
            }}
        """)
        header_layout.addWidget(self.search_box)
        
        # Refresh button
        refresh_btn = QPushButton("↻ Refresh")
        refresh_btn.clicked.connect(self.load_objects)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {colors['primary']};
                color: white;
                border-radius: 6px;
                padding: 8px 15px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {colors['primary_hover']};
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
        
        # Style table
        self.table.setStyleSheet(f"""
            QTableWidget {{
                border: 2px solid {colors['border']};
                border-radius: 8px;
                background-color: {colors['bg_widget']};
                gridline-color: {colors['border']};
                color: {colors['text']};
            }}
            QTableWidget::item {{
                padding: 8px;
                color: {colors['text']};
            }}
            QTableWidget::item:selected {{
                background-color: {colors['primary']};
                color: white;
            }}
            QHeaderView::section {{
                background-color: {colors['primary']};
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }}
        """)
        
        layout.addWidget(self.table)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet(f"color: {colors['text_secondary']}; font-size: 12px;")
        layout.addWidget(self.status_label)
        
        # Store colors for later use
        self.colors = colors
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        # Share selected button
        self.share_selected_btn = QPushButton("Share Selected")
        self.share_selected_btn.clicked.connect(self.share_selected)
        self.share_selected_btn.setEnabled(False)
        self.share_selected_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        button_layout.addWidget(self.share_selected_btn)
        
        button_layout.addStretch()
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
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
        self.objects = objects
        self.populate_table(objects)
        
        count = len(objects)
        total_size = sum(obj.get('bytes', 0) for obj in objects)
        size_text = self.format_size(total_size)
        
        self.status_label.setText(f"Loaded {count} objects ({size_text})")
    
    def on_load_error(self, error_msg):
        """Handle loading error."""
        self.loading_bar.hide()
        self.status_label.setText("Error loading objects")
        QMessageBox.critical(
            self,
            "Error",
            f"Failed to load bucket contents:\n{error_msg}"
        )
    
    def populate_table(self, objects):
        """Populate table with objects."""
        self.table.setRowCount(len(objects))
        
        for row, obj in enumerate(objects):
            # Name
            name_item = QTableWidgetItem(obj.get('name', ''))
            self.table.setItem(row, 0, name_item)
            
            # Size
            size = obj.get('bytes', 0)
            size_item = QTableWidgetItem(self.format_size(size))
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 1, size_item)
            
            # Last Modified
            last_modified = obj.get('last_modified', 'Unknown')
            time_item = QTableWidgetItem(last_modified)
            self.table.setItem(row, 2, time_item)
            
            # Actions button
            share_btn = QPushButton("Share")
            share_btn.setFixedSize(70, 28)  # Fixed size for consistency
            share_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-weight: bold;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """)
            share_btn.clicked.connect(
                lambda checked, name=obj.get('name'): self.share_single(name)
            )
            self.table.setCellWidget(row, 3, share_btn)
    
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
                f"Share Selected ({selected_rows})"
            )
        else:
            self.share_selected_btn.setText("Share Selected")
    
    def get_selected_objects(self):
        """Get list of selected object names."""
        selected_rows = self.table.selectionModel().selectedRows()
        object_names = []
        
        for index in selected_rows:
            row = index.row()
            name_item = self.table.item(row, 0)
            if name_item:
                object_names.append(name_item.text())
        
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
        
        object_name = name_item.text()
        
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
        
        # Add actions
        share_action = menu.addAction("Share this file")
        copy_name_action = menu.addAction("Copy filename")
        
        menu.addSeparator()
        
        share_all_action = menu.addAction("Share all selected files")
        
        # Execute menu and handle action
        action = menu.exec(QCursor.pos())
        
        if action == share_action:
            self.share_single(object_name)
        elif action == copy_name_action:
            from PyQt6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(object_name)
            self.status_label.setText(f"Copied: {object_name}")
        elif action == share_all_action:
            self.share_selected()
    
    def format_size(self, bytes_size: int) -> str:
        """Format bytes to human readable size."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} PB"
