"""
Interactive menu components using Rich prompts.
"""

from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich import box

from ..core.models import Chapter, DownloadConfig, OutputFormat
from ..utils.config import ConfigManager

console = Console()


class MainMenu:
    """Main application menu."""
    
    MENU_OPTIONS = {
        "1": ("📥 Download Manga by URL", "download"),
        "2": ("⚙️  Settings", "settings"),
        "3": ("🚪 Exit", "exit")
    }
    
    @classmethod
    def show(cls) -> str:
        """Show main menu and return selected action."""
        menu_text = "\n".join(
            f"  [cyan bold]{key}[/] │ {name}"
            for key, (name, _) in cls.MENU_OPTIONS.items()
        )
        
        panel = Panel(
            menu_text,
            title="[bold magenta]Main Menu[/]",
            border_style="magenta",
            box=box.ROUNDED
        )
        console.print(panel)
        
        while True:
            choice = Prompt.ask(
                "\n[bold cyan]Select an option[/]",
                choices=list(cls.MENU_OPTIONS.keys()),
                default="1"
            )
            
            if choice in cls.MENU_OPTIONS:
                return cls.MENU_OPTIONS[choice][1]
    
    @staticmethod
    def get_manga_url() -> str:
        """Prompt for manga URL."""
        return Prompt.ask(
            "\n[bold cyan]Enter manga URL[/]",
            default=""
        ).strip()


class ChapterSelector:
    """Chapter selection menu."""
    
    @staticmethod
    def select_chapters(chapters: list[Chapter]) -> list[Chapter]:
        """
        Prompt user to select chapters.
        
        Supports:
        - Single: "5"
        - Range: "1-10"
        - All: "all"
        - Multiple: "1,3,5-10"
        """
        console.print("\n[bold cyan]Chapter Selection Options:[/]")
        console.print("  • Enter a single number: [dim]5[/]")
        console.print("  • Enter a range: [dim]1-10[/]")
        console.print("  • Enter multiple: [dim]1,3,5-10[/]")
        console.print("  • Download all: [dim]all[/]")
        
        while True:
            selection = Prompt.ask(
                "\n[bold cyan]Select chapters[/]",
                default="all"
            ).strip().lower()
            
            if selection == "all":
                if Confirm.ask(
                    f"[yellow]Download all {len(chapters)} chapters?[/]",
                    default=True
                ):
                    return chapters
                continue
            
            try:
                selected = ChapterSelector._parse_selection(selection, chapters)
                if selected:
                    console.print(
                        f"[green]Selected {len(selected)} chapter(s): "
                        f"{', '.join(str(c.number) for c in selected[:5])}"
                        f"{'...' if len(selected) > 5 else ''}[/]"
                    )
                    if Confirm.ask("[cyan]Proceed with download?[/]", default=True):
                        return selected
                else:
                    console.print("[red]No valid chapters selected. Try again.[/]")
            except ValueError as e:
                console.print(f"[red]Invalid selection: {e}[/]")
    
    @staticmethod
    def _parse_selection(selection: str, chapters: list[Chapter]) -> list[Chapter]:
        """Parse chapter selection string."""
        # Create a mapping from chapter number to chapter object
        chapter_map = {str(ch.number): ch for ch in chapters}
        # Also create index-based mapping (1-indexed)
        index_map = {str(i): ch for i, ch in enumerate(chapters, 1)}
        
        selected = []
        parts = selection.replace(" ", "").split(",")
        
        for part in parts:
            if "-" in part:
                # Range selection
                start_str, end_str = part.split("-", 1)
                
                # Try as index first, then as chapter number
                try:
                    start = int(start_str)
                    end = int(end_str)
                    
                    # Check if these are indices
                    if str(start) in index_map and str(end) in index_map:
                        for i in range(start, end + 1):
                            if str(i) in index_map:
                                selected.append(index_map[str(i)])
                    else:
                        # Try as chapter numbers
                        for ch in chapters:
                            try:
                                ch_num = float(ch.number)
                                if start <= ch_num <= end:
                                    selected.append(ch)
                            except (ValueError, TypeError):
                                pass
                except ValueError:
                    raise ValueError(f"Invalid range: {part}")
            else:
                # Single selection - try index first, then chapter number
                if part in index_map:
                    selected.append(index_map[part])
                elif part in chapter_map:
                    selected.append(chapter_map[part])
                else:
                    # Try to match chapter number more flexibly
                    for ch in chapters:
                        if str(ch.number) == part:
                            selected.append(ch)
                            break
        
        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for ch in selected:
            if ch.chapter_id not in seen:
                seen.add(ch.chapter_id)
                unique.append(ch)
        
        return unique


class SettingsMenu:
    """Settings configuration menu."""
    
    @staticmethod
    def show(config_manager: ConfigManager) -> bool:
        """
        Show settings menu and handle changes.
        
        Returns:
            True to return to main menu
        """
        while True:
            config = config_manager.get_download_config()
            
            console.print("\n[bold magenta]⚙️  Settings Menu[/]\n")
            
            options = [
                f"  [cyan bold]1[/] │ Output Format: [white]{config.output_format.value.upper()}[/]",
                f"  [cyan bold]2[/] │ Keep Images After Conversion: [white]{'✅ Yes' if config.keep_images else '❌ No'}[/]",
                f"  [cyan bold]3[/] │ Enable Logs: [white]{'✅ Yes' if config.enable_logs else '❌ No'}[/]",
                f"  [cyan bold]4[/] │ Download Path: [white]{config.download_path}[/]",
                f"  [cyan bold]5[/] │ Max Chapter Workers: [white]{config.max_chapter_workers}[/]",
                f"  [cyan bold]6[/] │ Max Image Workers: [white]{config.max_image_workers}[/]",
                f"  [cyan bold]7[/] │ Reset to Defaults",
                f"  [cyan bold]0[/] │ Back to Main Menu",
            ]
            
            panel = Panel(
                "\n".join(options),
                border_style="yellow",
                box=box.ROUNDED
            )
            console.print(panel)
            
            choice = Prompt.ask(
                "\n[bold cyan]Select option to change[/]",
                choices=["0", "1", "2", "3", "4", "5", "6", "7"],
                default="0"
            )
            
            if choice == "0":
                return True
            
            elif choice == "1":
                # Output format
                format_choice = Prompt.ask(
                    "[cyan]Select format[/]",
                    choices=["images", "pdf", "cbz"],
                    default=config.output_format.value
                )
                config_manager.set("output_format", format_choice)
                console.print(f"[green]Output format set to: {format_choice.upper()}[/]")
            
            elif choice == "2":
                # Keep images
                keep = Confirm.ask(
                    "[cyan]Keep images after PDF/CBZ conversion?[/]",
                    default=config.keep_images
                )
                config_manager.set("keep_images", keep)
                console.print(f"[green]Keep images: {'Yes' if keep else 'No'}[/]")
            
            elif choice == "3":
                # Enable logs
                enable = Confirm.ask(
                    "[cyan]Enable logging?[/]",
                    default=config.enable_logs
                )
                config_manager.set("enable_logs", enable)
                console.print(f"[green]Logging: {'Enabled' if enable else 'Disabled'}[/]")
            
            elif choice == "4":
                # Download path
                path = Prompt.ask(
                    "[cyan]Enter download path[/]",
                    default=config.download_path
                )
                config_manager.set("download_path", path)
                console.print(f"[green]Download path set to: {path}[/]")
            
            elif choice == "5":
                # Max chapter workers
                workers = IntPrompt.ask(
                    "[cyan]Max concurrent chapter downloads (1-10)[/]",
                    default=config.max_chapter_workers
                )
                workers = max(1, min(10, workers))
                config_manager.set("max_chapter_workers", workers)
                console.print(f"[green]Max chapter workers: {workers}[/]")
            
            elif choice == "6":
                # Max image workers
                workers = IntPrompt.ask(
                    "[cyan]Max concurrent image downloads (1-20)[/]",
                    default=config.max_image_workers
                )
                workers = max(1, min(20, workers))
                config_manager.set("max_image_workers", workers)
                console.print(f"[green]Max image workers: {workers}[/]")
            
            elif choice == "7":
                # Reset to defaults
                if Confirm.ask("[yellow]Reset all settings to defaults?[/]", default=False):
                    config_manager.reset_to_defaults()
                    console.print("[green]Settings reset to defaults![/]")
