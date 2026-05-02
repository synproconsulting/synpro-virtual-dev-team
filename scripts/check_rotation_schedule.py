#!/usr/bin/env python3
"""
scripts/check_rotation_schedule.py
==================================
Check token rotation schedule and send notifications for upcoming rotations.

Usage:
    ./scripts/check_rotation_schedule.py --notify
    ./scripts/check_rotation_schedule.py --report
    ./scripts/check_rotation_schedule.py --update jwt --rotated-date 2024-01-15

Author: DevOps Team
Created: 2024-01-XX
Ticket: SDT1-70
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Rotation schedule configuration
ROTATION_SCHEDULE_FILE = Path('config/rotation_schedule.json')

# Default rotation frequencies (in days)
DEFAULT_FREQUENCIES = {
    'jwt': 90,
    'database': 180,
    'railway': 60,
    'smtp': 180,
    'jira': 90,
}


class RotationSchedule:
    """Manage token rotation schedule."""
    
    def __init__(self, schedule_file: Path = ROTATION_SCHEDULE_FILE):
        """
        Initialize rotation schedule.
        
        Args:
            schedule_file: Path to schedule JSON file
        """
        self.schedule_file = schedule_file
        self.schedule = self._load_schedule()
    
    def _load_schedule(self) -> Dict:
        """Load rotation schedule from file."""
        if not self.schedule_file.exists():
            # Create default schedule
            self.schedule_file.parent.mkdir(parents=True, exist_ok=True)
            default_schedule = {
                'version': '1.0',
                'last_updated': datetime.now().isoformat(),
                'tokens': {}
            }
            self._save_schedule(default_schedule)
            return default_schedule
        
        with open(self.schedule_file, 'r') as f:
            return json.load(f)
    
    def _save_schedule(self, schedule: Dict) -> None:
        """Save rotation schedule to file."""
        schedule['last_updated'] = datetime.now().isoformat()
        with open(self.schedule_file, 'w') as f:
            json.dump(schedule, f, indent=2)
    
    def get_token_info(self, token_type: str) -> Dict:
        """
        Get information about a token.
        
        Args:
            token_type: Type of token
            
        Returns:
            Token information dictionary
        """
        if token_type not in self.schedule['tokens']:
            # Create default entry
            frequency = DEFAULT_FREQUENCIES.get(token_type, 90)
            self.schedule['tokens'][token_type] = {
                'last_rotated': None,
                'rotation_frequency_days': frequency,
                'next_rotation_due': None,
                'rotation_history': []
            }
            self._save_schedule(self.schedule)
        
        return self.schedule['tokens'][token_type]
    
    def update_rotation(self, token_type: str, rotated_date: Optional[datetime] = None) -> None:
        """
        Update token rotation date.
        
        Args:
            token_type: Type of token
            rotated_date: Date rotated (default: now)
        """
        token_info = self.get_token_info(token_type)
        
        if rotated_date is None:
            rotated_date = datetime.now()
        
        # Update last rotated
        token_info['last_rotated'] = rotated_date.isoformat()
        
        # Calculate next rotation due date
        frequency = token_info['rotation_frequency_days']
        next_due = rotated_date + timedelta(days=frequency)
        token_info['next_rotation_due'] = next_due.isoformat()
        
        # Add to history
        token_info['rotation_history'].append({
            'date': rotated_date.isoformat(),
            'scheduled': False  # Could be enhanced to track if it was on schedule
        })
        
        # Keep only last 10 rotations in history
        if len(token_info['rotation_history']) > 10:
            token_info['rotation_history'] = token_info['rotation_history'][-10:]
        
        self._save_schedule(self.schedule)
        print(f"✓ Updated rotation schedule for {token_type}")
        print(f"  Last rotated: {rotated_date.date()}")
        print(f"  Next due: {next_due.date()}")
    
    def get_upcoming_rotations(self, days_ahead: int = 30) -> List[Tuple[str, datetime, int]]:
        """
        Get tokens that need rotation soon.
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List of (token_type, due_date, days_until_due)
        """
        upcoming = []
        now = datetime.now()
        
        for token_type in DEFAULT_FREQUENCIES.keys():
            token_info = self.get_token_info(token_type)
            
            if token_info['next_rotation_due']:
                due_date = datetime.fromisoformat(token_info['next_rotation_due'])
                days_until = (due_date - now).days
                
                if days_until <= days_ahead:
                    upcoming.append((token_type, due_date, days_until))
        
        # Sort by days until due
        upcoming.sort(key=lambda x: x[2])
        return upcoming
    
    def get_overdue_rotations(self) -> List[Tuple[str, datetime, int]]:
        """
        Get tokens that are overdue for rotation.
        
        Returns:
            List of (token_type, due_date, days_overdue)
        """
        overdue = []
        now = datetime.now()
        
        for token_type in DEFAULT_FREQUENCIES.keys():
            token_info = self.get_token_info(token_type)
            
            if token_info['next_rotation_due']:
                due_date = datetime.fromisoformat(token_info['next_rotation_due'])
                days_until = (due_date - now).days
                
                if days_until < 0:
                    overdue.append((token_type, due_date, abs(days_until)))
        
        # Sort by days overdue (most overdue first)
        overdue.sort(key=lambda x: x[2], reverse=True)
        return overdue
    
    def generate_report(self) -> str:
        """
        Generate rotation status report.
        
        Returns:
            Report as string
        """
        lines = []
        lines.append("\n" + "=" * 80)
        lines.append("Token Rotation Status Report")
        lines.append("=" * 80)
        lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Overdue rotations
        overdue = self.get_overdue_rotations()
        if overdue:
            lines.append("\n⚠️  OVERDUE ROTATIONS:")
            lines.append("-" * 80)
            for token_type, due_date, days_overdue in overdue:
                lines.append(f"  • {token_type.upper():<15} - {days_overdue} days overdue (due: {due_date.date()})")
        else:
            lines.append("\n✓ No overdue rotations")
        
        # Upcoming rotations (next 30 days)
        upcoming = self.get_upcoming_rotations(days_ahead=30)
        if upcoming:
            lines.append("\n📅 UPCOMING ROTATIONS (next 30 days):")
            lines.append("-" * 80)
            for token_type, due_date, days_until in upcoming:
                if days_until >= 0:
                    lines.append(f"  • {token_type.upper():<15} - in {days_until} days ({due_date.date()})")
        
        # All token status
        lines.append("\n📊 ALL TOKENS:")
        lines.append("-" * 80)
        lines.append(f"{'Token Type':<15} {'Last Rotated':<15} {'Next Due':<15} {'Frequency':<12} {'Status'}")
        lines.append("-" * 80)
        
        for token_type in sorted(DEFAULT_FREQUENCIES.keys()):
            token_info = self.get_token_info(token_type)
            
            last_rotated = 'Never'
            if token_info['last_rotated']:
                last_date = datetime.fromisoformat(token_info['last_rotated'])
                last_rotated = last_date.strftime('%Y-%m-%d')
            
            next_due = 'Not set'
            status = '⚪ Not scheduled'
            if token_info['next_rotation_due']:
                due_date = datetime.fromisoformat(token_info['next_rotation_due'])
                next_due = due_date.strftime('%Y-%m-%d')
                
                days_until = (due_date - datetime.now()).days
                if days_until < 0:
                    status = f'🔴 {abs(days_until)}d overdue'
                elif days_until <= 7:
                    status = f'🟡 {days_until}d remaining'
                elif days_until <= 30:
                    status = f'🟢 {days_until}d remaining'
                else:
                    status = f'🟢 {days_until}d remaining'
            
            frequency = f"{token_info['rotation_frequency_days']}d"
            
            lines.append(f"{token_type.upper():<15} {last_rotated:<15} {next_due:<15} {frequency:<12} {status}")
        
        lines.append("\n" + "=" * 80)
        lines.append("\nFor rotation procedures, see: docs/runbooks/TOKEN_ROTATION.md")
        lines.append("To rotate a token: ./scripts/rotate_token.py --env production --token-type <type>")
        lines.append("")
        
        return "\n".join(lines)
    
    def send_notifications(self, webhook_url: Optional[str] = None) -> None:
        """
        Send notifications for upcoming rotations.
        
        Args:
            webhook_url: Slack/Discord webhook URL (optional)
        """
        overdue = self.get_overdue_rotations()
        upcoming = self.get_upcoming_rotations(days_ahead=7)
        
        if not overdue and not upcoming:
            print("✓ No notifications needed (all rotations are on schedule)")
            return
        
        # Print to console
        if overdue:
            print("\n⚠️  OVERDUE ROTATIONS:")
            for token_type, due_date, days_overdue in overdue:
                print(f"  • {token_type.upper()} - {days_overdue} days overdue")
        
        if upcoming:
            print("\n📅 UPCOMING ROTATIONS (next 7 days):")
            for token_type, due_date, days_until in upcoming:
                if days_until >= 0:
                    print(f"  • {token_type.upper()} - due in {days_until} days")
        
        # Send to webhook if provided
        if webhook_url:
            try:
                import requests
                
                message = "🔐 **Token Rotation Reminder**\n\n"
                
                if overdue:
                    message += "⚠️ **OVERDUE:**\n"
                    for token_type, due_date, days_overdue in overdue:
                        message += f"• {token_type.upper()}: {days_overdue} days overdue\n"
                    message += "\n"
                
                if upcoming:
                    message += "📅 **UPCOMING (next 7 days):**\n"
                    for token_type, due_date, days_until in upcoming:
                        if days_until >= 0:
                            message += f"• {token_type.upper()}: due in {days_until} days\n"
                
                message += "\nSee runbook: docs/runbooks/TOKEN_ROTATION.md"
                
                payload = {'text': message}
                response = requests.post(webhook_url, json=payload, timeout=10)
                
                if response.status_code == 200:
                    print("\n✓ Notification sent to webhook")
                else:
                    print(f"\n✗ Failed to send webhook notification: {response.status_code}")
            
            except Exception as e:
                print(f"\n✗ Error sending webhook notification: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Check token rotation schedule and send notifications',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate rotation status report
  %(prog)s --report
  
  # Check and send notifications
  %(prog)s --notify
  
  # Send to Slack webhook
  %(prog)s --notify --webhook https://hooks.slack.com/...
  
  # Update rotation date for JWT token
  %(prog)s --update jwt --rotated-date 2024-01-15
  
  # Mark token as rotated today
  %(prog)s --update database
        """
    )
    
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate rotation status report'
    )
    
    parser.add_argument(
        '--notify',
        action='store_true',
        help='Send notifications for upcoming rotations'
    )
    
    parser.add_argument(
        '--webhook',
        help='Slack/Discord webhook URL for notifications'
    )
    
    parser.add_argument(
        '--update',
        choices=['jwt', 'database', 'railway', 'smtp', 'jira'],
        help='Update rotation date for a token'
    )
    
    parser.add_argument(
        '--rotated-date',
        help='Rotation date (YYYY-MM-DD), default: today'
    )
    
    parser.add_argument(
        '--days-ahead',
        type=int,
        default=7,
        help='Days ahead to check for upcoming rotations (default: 7)'
    )
    
    args = parser.parse_args()
    
    if not any([args.report, args.notify, args.update]):
        parser.error("Must specify --report, --notify, or --update")
    
    try:
        schedule = RotationSchedule()
        
        if args.update:
            # Update rotation date
            rotated_date = None
            if args.rotated_date:
                rotated_date = datetime.strptime(args.rotated_date, '%Y-%m-%d')
            
            schedule.update_rotation(args.update, rotated_date)
        
        if args.report:
            # Generate and print report
            report = schedule.generate_report()
            print(report)
        
        if args.notify:
            # Send notifications
            schedule.send_notifications(webhook_url=args.webhook)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
