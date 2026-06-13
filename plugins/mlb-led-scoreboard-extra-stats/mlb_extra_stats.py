# import time
# import requests
# import os
# from datetime import datetime, timedelta
# from bullpen.api import UpdateStatus

# # --- SHARED CONFIG ---
# class ScheduleConfig:
#     def __init__(self, plugin_config):
#         self.team_id = 112
#         self.update_interval = 1800
#         self.war_positions = ['SS', '2B', '3B', '1B', 'C', 'CF', 'RF', 'LF', 'DH']
#         if plugin_config:
#             self.team_id = getattr(plugin_config, 'team_id', 112)

# # --- 1. SCHEDULE DATA ---
# class ScheduleData:
#     def __init__(self, config):
#         self.config, self.last_update = config, 0
#         self.last_five, self.next_five = [], []

#     def update(self):
#         if time.time() - self.last_update < self.config.update_interval:
#             return UpdateStatus.DEFERRED
#         try:
#             now = datetime.now()
#             start = (now - timedelta(days=14)).strftime('%Y-%m-%d')
#             end = (now + timedelta(days=14)).strftime('%Y-%m-%d')
#             url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={self.config.team_id}&startDate={start}&endDate={end}&hydrate=team,linescore"
#             res = requests.get(url, timeout=10).json()
#             all_g = [g for d in res.get('dates', []) for g in d.get('games', [])]
            
#             fin = [g for g in all_g if g.get('status', {}).get('abstractGameState') == 'Final']
#             fin.reverse()
#             self.last_five = []
#             for g in fin[:5]:
#                 t = g.get('teams', {})
#                 is_away = t.get('away', {}).get('team', {}).get('id') == self.config.team_id
#                 s, o_s = ('away', 'home') if is_away else ('home', 'away')
#                 self.last_five.append({
#                     "is_away": is_away,
#                     "opp": t.get(o_s, {}).get('team', {}).get('abbreviation', '??'),
#                     "score": f"{t.get(s, {}).get('score', 0)}-{t.get(o_s, {}).get('score', 0)}",
#                     "res": "W" if t.get(s, {}).get('score', 0) > t.get(o_s, {}).get('score', 0) else "L"
#                 })
#             upc = [g for g in all_g if g.get('status', {}).get('abstractGameState') in ['Preview', 'Live']]
#             self.next_five = []
#             for g in upc[:5]:
#                 t = g.get('teams', {})
#                 is_away = t.get('away', {}).get('team', {}).get('id') == self.config.team_id
#                 o_s = 'home' if is_away else 'away'
#                 g_dt = datetime.strptime(g.get('gameDate'), '%Y-%m-%dT%H:%M:%SZ') - timedelta(hours=5)
#                 self.next_five.append({
#                     "is_away": is_away, "date": g_dt.strftime('%m/%d'),
#                     "opp": t.get(o_s, {}).get('team', {}).get('abbreviation', '??'),
#                     "time": g_dt.strftime('%I:%M%p').lower().lstrip('0').replace('m', '')
#                 })
#             self.last_update = time.time()
#             return UpdateStatus.SUCCESS
#         except: return UpdateStatus.FAILED

# # --- 2. WAR LEADER DATA (FanGraphs) ---
# class WARData:
#     def __init__(self, config):
#         self.config, self.last_update = config, 0
#         self.pos_data = {}

#     def update(self):
#         if time.time() - self.last_update < 43200:
#             return UpdateStatus.DEFERRED
#         try:
#             current_year = datetime.now().year
#             headers = {"User-Agent": "MLB-LED-Scoreboard-Plugin/1.0"}
            
#             for pos in self.config.war_positions:
#                 url = f"https://www.fangraphs.com/api/leaders/major-league/data?age=&pos={pos.lower()}&stats=bat&lg=all&qual=y&season={current_year}&season1={current_year}&ind=0&pageitems=3"
#                 res = requests.get(url, headers=headers, timeout=10).json()
#                 leaders = []
#                 for p in res.get('data', []):
#                     name_parts = p.get('PlayerName', '??').split(' ')
#                     last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else name_parts[0]
#                     # Map to 'val' for universal rendering
#                     leaders.append({"name": last_name, "val": f"{p.get('WAR', 0.0):.1f}"})
#                 self.pos_data[pos] = leaders
#             self.last_update = time.time()
#             return UpdateStatus.SUCCESS
#         except: return UpdateStatus.FAILED

# # --- 3. STAT LEADERS DATA (MLB API) ---
# class StatLeadersData:
#     def __init__(self, config):
#         self.config, self.last_update = config, 0
#         self.leaders = {}

#     def update(self):
#         if time.time() - self.last_update < 21600:
#             return UpdateStatus.DEFERRED
#         try:
#             year = datetime.now().year
            
#             hit_cats = "homeRuns,onBasePlusSlugging,battingAverage,runsBattedIn,stolenBases"
#             hit_url = f"https://statsapi.mlb.com/api/v1/stats/leaders?leaderCategories={hit_cats}&statGroup=hitting&limit=3&season={year}"
            
#             pitch_cats = "earnedRunAverage,strikeouts"
#             pitch_url = f"https://statsapi.mlb.com/api/v1/stats/leaders?leaderCategories={pitch_cats}&statGroup=pitching&limit=3&season={year}"
            
#             for url in [hit_url, pitch_url]:
#                 res = requests.get(url, timeout=10).json()
#                 for cg in res.get('leagueLeaders', []):
#                     cat = cg.get('leaderCategory')
#                     cat_leaders = []
#                     for l in cg.get('leaders', []):
#                         name = l.get('person', {}).get('lastName', '??')
#                         val = str(l.get('value', '0'))
                        
#                         # Strip leading zero for AVG and OPS to save space (0.330 -> .330)
#                         if val.startswith("0."):
#                             val = val[1:]
                            
#                         cat_leaders.append({"name": name, "val": val})
#                     self.leaders[cat] = cat_leaders
            
#             self.last_update = time.time()
#             return UpdateStatus.SUCCESS
#         except Exception as e: 
#             print(f"Stat Leaders Error: {e}")
#             return UpdateStatus.FAILED

# # --- RENDERERS ---
# class BaseRenderer:
#     def __init__(self, config, layout, colors):
#         self.config, self.layout, self.f = config, layout, None

#     def get_font(self, graphics):
#         if self.f: return self.f
#         self.f = graphics.Font()
#         p = os.path.join(os.getcwd(), 'assets', 'fonts', 'patched', '4x6.bdf')
#         if not os.path.exists(p): p = os.path.join(os.getcwd(), 'assets', 'fonts', '4x6.bdf')
#         self.f.LoadFont(p)
#         return self.f
        
#     def reset(self): pass

#     def draw_leaderboard(self, canvas, graphics, title, leaders, start_time):
#         canvas.Fill(0, 0, 0)
#         font = self.get_font(graphics)
#         w, g, gold = graphics.Color(255, 255, 255), graphics.Color(150, 150, 150), graphics.Color(255, 200, 0)
#         black = graphics.Color(0, 0, 0)
        
#         # 1. Title
#         graphics.DrawText(canvas, font, 2, 6, gold, title)

#         # 2. DYNAMIC SPACING MATH
#         # Find the max width of the stat values (e.g., OPS "1.061" = 5 chars. HR "28" = 2 chars)
#         max_val_len = max(len(str(p['val'])) for p in leaders) if leaders else 3
        
#         # Calculate exactly where the stat should start to touch the right edge (x=63)
#         # 4 pixels per char + 1 px right padding
#         stat_x = 64 - (max_val_len * 4) - 1 
        
#         # Mask hides scrolling text just before the stat starts
#         right_mask_start = stat_x - 2
#         name_start_x = 12
#         visible_name_width = right_mask_start - name_start_x

#         # 3. Draw Names (Scrolling if necessary)
#         y = 14
#         for p in leaders:
#             name = p['name']
#             name_width = len(name) * 4 
#             name_x = name_start_x
            
#             if name_width > visible_name_width:
#                 elapsed = time.time() - start_time
#                 shift = int(elapsed * 8) # Slower, readable scroll speed
#                 total_scroll = name_width - visible_name_width
                
#                 # Smooth Ping-Pong Animation (Pause -> Slide -> Pause -> Slide)
#                 pause = 16 # Approx 2 seconds
#                 cycle = (total_scroll * 2) + (pause * 2) 
#                 frame = shift % cycle
                
#                 if frame < pause: 
#                     offset = 0
#                 elif frame < pause + total_scroll: 
#                     offset = frame - pause
#                 elif frame < (pause * 2) + total_scroll: 
#                     offset = total_scroll
#                 else: 
#                     offset = total_scroll - (frame - (pause * 2) - total_scroll)
                    
#                 name_x = name_start_x - offset
                
#             graphics.DrawText(canvas, font, name_x, y, w, name)
#             y += 8
            
#         # 4. Draw Black Masking Rectangles over the left and right edges
#         for y_line in range(7, 32):
#             # Left Mask (covers x=0 to x=11, hiding text before the "1. ")
#             graphics.DrawLine(canvas, 0, y_line, name_start_x - 1, y_line, black)
#             # Right Mask (covers text passing behind the stat value)
#             graphics.DrawLine(canvas, right_mask_start, y_line, 63, y_line, black)
            
#         # 5. Draw Static Rank and Stat Value ON TOP of the masks
#         y = 14
#         for i, p in enumerate(leaders):
#             graphics.DrawText(canvas, font, 2, y, g, f"{i+1}.")
#             # Note: Stat value is now drawn in Gray (g)
#             graphics.DrawText(canvas, font, stat_x, y, g, str(p['val']))
#             y += 8

# class LastFiveRenderer(BaseRenderer):
#     def can_render(self, d): return len(d.last_five) > 0
#     def wait_time(self): return 3.0
#     def render(self, d, canvas, graphics, pos):
#         canvas.Fill(0, 0, 0)
#         font = self.get_font(graphics)
#         h, a = graphics.Color(255, 255, 255), graphics.Color(180, 180, 180)
#         y = 6
#         for g in d.last_five:
#             c = a if g['is_away'] else h
#             graphics.DrawText(canvas, font, 4, y, c, g['opp'])
#             graphics.DrawText(canvas, font, 28, y, c, g['score'])
#             graphics.DrawText(canvas, font, 54, y, c, g['res'])
#             y += 6
#         return None

# class NextFiveRenderer(BaseRenderer):
#     def can_render(self, d): return len(d.next_five) > 0
#     def wait_time(self): return 3.0
#     def render(self, d, canvas, graphics, pos):
#         canvas.Fill(0, 0, 0)
#         font = self.get_font(graphics)
#         h, a = graphics.Color(255, 255, 255), graphics.Color(180, 180, 180)
#         y = 6
#         for g in d.next_five:
#             c = a if g['is_away'] else h
#             graphics.DrawText(canvas, font, 1, y, c, g['date'])
#             graphics.DrawText(canvas, font, 25, y, c, g['opp'])
#             graphics.DrawText(canvas, font, 41, y, c, g['time'])
#             y += 6
#         return None

# class WARRenderer(BaseRenderer):
#     def __init__(self, config, layout, colors):
#         super().__init__(config, layout, colors)
#         self.start_time = 0
#     def can_render(self, d): return len(d.pos_data) > 0
#     def wait_time(self): return 0.04
#     def reset(self): self.start_time = 0
    
#     def render(self, d, canvas, graphics, pos):
#         if self.start_time == 0: self.start_time = time.time()
        
#         elapsed = time.time() - self.start_time
#         idx = int(elapsed // 6)
        
#         if idx >= len(self.config.war_positions): return None 

#         curr_pos = self.config.war_positions[idx]
#         leaders = d.pos_data.get(curr_pos, [])
#         title = f"TOP {curr_pos} (WAR)"
        
#         screen_start_time = self.start_time + (idx * 6)
#         self.draw_leaderboard(canvas, graphics, title, leaders, screen_start_time)
#         return 0

# # --- SCROLLING STAT RENDERER ---
# class StatRenderer(BaseRenderer):
#     def __init__(self, config, layout, colors, metric_key, title):
#         super().__init__(config, layout, colors)
#         self.metric_key = metric_key
#         self.title = title
#         self.start_time = 0

#     def can_render(self, d):
#         return len(d.leaders.get(self.metric_key, [])) > 0

#     def wait_time(self): return 0.04 

#     def reset(self): self.start_time = 0

#     def render(self, d, canvas, graphics, pos):
#         if self.start_time == 0: self.start_time = time.time()
#         leaders = d.leaders.get(self.metric_key, [])
#         self.draw_leaderboard(canvas, graphics, self.title, leaders, self.start_time)
#         return 0

# # Subclasses to create the entry points
# class HRRenderer(StatRenderer):
#     def __init__(self, c, l, col): super().__init__(c, l, col, 'homeRuns', 'MLB HR LEADERS')
# class OPSRenderer(StatRenderer):
#     def __init__(self, c, l, col): super().__init__(c, l, col, 'onBasePlusSlugging', 'MLB OPS LEADERS')
# class AVGRenderer(StatRenderer):
#     def __init__(self, c, l, col): super().__init__(c, l, col, 'battingAverage', 'MLB AVG LEADERS')
# class RBIRenderer(StatRenderer):
#     def __init__(self, c, l, col): super().__init__(c, l, col, 'runsBattedIn', 'MLB RBI LEADERS')
# class SBRenderer(StatRenderer):
#     def __init__(self, c, l, col): super().__init__(c, l, col, 'stolenBases', 'MLB SB LEADERS')
# class ERARenderer(StatRenderer):
#     def __init__(self, c, l, col): super().__init__(c, l, col, 'earnedRunAverage', 'MLB ERA LEADERS')
# class KRenderer(StatRenderer):
#     def __init__(self, c, l, col): super().__init__(c, l, col, 'strikeouts', 'MLB K LEADERS')

# # --- EXPORTS ---
# def load_last_five(): return (ScheduleConfig, ScheduleData, LastFiveRenderer)
# def load_next_five(): return (ScheduleConfig, ScheduleData, NextFiveRenderer)
# def load_war_leaders(): return (ScheduleConfig, WARData, WARRenderer)
# def load_hr_leaders(): return (ScheduleConfig, StatLeadersData, HRRenderer)
# def load_ops_leaders(): return (ScheduleConfig, StatLeadersData, OPSRenderer)
# def load_avg_leaders(): return (ScheduleConfig, StatLeadersData, AVGRenderer)
# def load_rbi_leaders(): return (ScheduleConfig, StatLeadersData, RBIRenderer)
# def load_sb_leaders(): return (ScheduleConfig, StatLeadersData, SBRenderer)
# def load_era_leaders(): return (ScheduleConfig, StatLeadersData, ERARenderer)
# def load_k_leaders(): return (ScheduleConfig, StatLeadersData, KRenderer)

import time
import requests
import os
from datetime import datetime, timedelta
from bullpen.api import UpdateStatus

# --- SHARED CONFIG ---
class ScheduleConfig:
    def __init__(self, plugin_config):
        # Bullpen passes plugin_config. Handle both dicts and objects just to be safe.
        def get_setting(key, default):
            if isinstance(plugin_config, dict):
                return plugin_config.get(key, default)
            return getattr(plugin_config, key, default) if plugin_config else default

        # Users can now easily change this in their config.json
        self.team_id = get_setting('team_id', 112) # Default: Cubs
        self.update_interval = get_setting('update_interval', 1800)
        self.war_positions = get_setting('war_positions', ['SS', '2B', '3B', '1B', 'C', 'CF', 'RF', 'LF', 'DH'])

        # Configurable Colors (Expected as [R, G, B] in config.json)
        self.color_title = get_setting('color_title', [255, 200, 0])       # Gold
        self.color_text = get_setting('color_text', [255, 255, 255])       # White
        self.color_rank = get_setting('color_rank', [150, 150, 150])       # Gray
        self.color_away = get_setting('color_away', [180, 180, 180])       # Light Gray

# --- 1. SCHEDULE DATA ---
class ScheduleData:
    _last_update = 0
    _last_five = []
    _next_five = []

    def __init__(self, config):
        self.config = config

    @property
    def last_five(self): return self.__class__._last_five

    @property
    def next_five(self): return self.__class__._next_five

    def update(self):
        cls = self.__class__
        if time.time() - cls._last_update < self.config.update_interval:
            return UpdateStatus.DEFERRED
        try:
            now = datetime.now()
            start = (now - timedelta(days=14)).strftime('%Y-%m-%d')
            end = (now + timedelta(days=14)).strftime('%Y-%m-%d')
            url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId={self.config.team_id}&startDate={start}&endDate={end}&hydrate=team,linescore"
            
            res = requests.get(url, timeout=5)
            res.raise_for_status() # Ensure valid HTTP status before parsing JSON
            res_data = res.json()
            
            all_g = [g for d in res_data.get('dates', []) for g in d.get('games', [])]
            
            fin = [g for g in all_g if g.get('status', {}).get('abstractGameState') == 'Final']
            fin.reverse()
            
            new_last_five = []
            for g in fin[:5]:
                t = g.get('teams', {})
                is_away = t.get('away', {}).get('team', {}).get('id') == self.config.team_id
                s, o_s = ('away', 'home') if is_away else ('home', 'away')
                new_last_five.append({
                    "is_away": is_away,
                    "opp": t.get(o_s, {}).get('team', {}).get('abbreviation', '??'),
                    "score": f"{t.get(s, {}).get('score', 0)}-{t.get(o_s, {}).get('score', 0)}",
                    "res": "W" if t.get(s, {}).get('score', 0) > t.get(o_s, {}).get('score', 0) else "L"
                })
            cls._last_five = new_last_five

            upc = [g for g in all_g if g.get('status', {}).get('abstractGameState') in ['Preview', 'Live']]
            new_next_five = []
            for g in upc[:5]:
                t = g.get('teams', {})
                is_away = t.get('away', {}).get('team', {}).get('id') == self.config.team_id
                o_s = 'home' if is_away else 'away'
                g_dt = datetime.strptime(g.get('gameDate'), '%Y-%m-%dT%H:%M:%SZ') - timedelta(hours=5)
                new_next_five.append({
                    "is_away": is_away, "date": g_dt.strftime('%m/%d'),
                    "opp": t.get(o_s, {}).get('team', {}).get('abbreviation', '??'),
                    "time": g_dt.strftime('%I:%M%p').lower().lstrip('0').replace('m', '')
                })
            cls._next_five = new_next_five
            
            cls._last_update = time.time()
            return UpdateStatus.SUCCESS
        except Exception as e:
            print(f"ScheduleData Error: {e}")
            return UpdateStatus.FAILED

# --- 2. WAR LEADER DATA (FanGraphs) ---
class WARData:
    _last_update = 0
    _pos_data = {}

    def __init__(self, config):
        self.config = config

    @property
    def pos_data(self): return self.__class__._pos_data

    def update(self):
        cls = self.__class__
        if time.time() - cls._last_update < 43200:
            return UpdateStatus.DEFERRED
        try:
            current_year = datetime.now().year
            headers = {"User-Agent": "MLB-LED-Scoreboard-Plugin/1.0"}
            
            new_pos_data = {}
            for pos in self.config.war_positions:
                url = f"https://www.fangraphs.com/api/leaders/major-league/data?age=&pos={pos.lower()}&stats=bat&lg=all&qual=y&season={current_year}&season1={current_year}&ind=0&pageitems=3"
                res = requests.get(url, headers=headers, timeout=5)
                res.raise_for_status()
                
                leaders = []
                for p in res.json().get('data', []):
                    name_parts = p.get('PlayerName', '??').split(' ')
                    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else name_parts[0]
                    leaders.append({"name": last_name, "val": f"{p.get('WAR', 0.0):.1f}"})
                new_pos_data[pos] = leaders
            
            cls._pos_data = new_pos_data
            cls._last_update = time.time()
            return UpdateStatus.SUCCESS
        except Exception as e: 
            print(f"WARData Error: {e}")
            return UpdateStatus.FAILED

# --- 3. STAT LEADERS DATA (MLB API) ---
class StatLeadersData:
    _last_update = 0
    _leaders = {}

    def __init__(self, config):
        self.config = config

    @property
    def leaders(self): return self.__class__._leaders

    def update(self):
        cls = self.__class__
        if time.time() - cls._last_update < 21600:
            return UpdateStatus.DEFERRED
        try:
            year = datetime.now().year
            new_leaders = {}
            
            hit_cats = "homeRuns,onBasePlusSlugging,battingAverage,runsBattedIn,stolenBases"
            hit_url = f"https://statsapi.mlb.com/api/v1/stats/leaders?leaderCategories={hit_cats}&statGroup=hitting&limit=3&season={year}"
            
            pitch_cats = "earnedRunAverage,strikeouts"
            pitch_url = f"https://statsapi.mlb.com/api/v1/stats/leaders?leaderCategories={pitch_cats}&statGroup=pitching&limit=3&season={year}"
            
            for url in [hit_url, pitch_url]:
                res = requests.get(url, timeout=5)
                res.raise_for_status()
                for cg in res.json().get('leagueLeaders', []):
                    cat = cg.get('leaderCategory')
                    cat_leaders = []
                    for l in cg.get('leaders', []):
                        name = l.get('person', {}).get('lastName', '??')
                        val = str(l.get('value', '0'))
                        if val.startswith("0."):
                            val = val[1:]
                        cat_leaders.append({"name": name, "val": val})
                    new_leaders[cat] = cat_leaders
            
            cls._leaders = new_leaders
            cls._last_update = time.time()
            return UpdateStatus.SUCCESS
        except Exception as e: 
            print(f"Stat Leaders Error: {e}")
            return UpdateStatus.FAILED

# --- RENDERERS ---
class BaseRenderer:
    def __init__(self, config, layout, colors):
        self.config, self.layout, self.colors = config, layout, colors
        self.f = None

    def get_font(self, graphics):
        if self.f: 
            return self.f
            
        self.f = graphics.Font()
        p = os.path.join(os.getcwd(), 'assets', 'fonts', 'patched', '4x6.bdf')
        if not os.path.exists(p): 
            p = os.path.join(os.getcwd(), 'assets', 'fonts', '4x6.bdf')
        self.f.LoadFont(p)
        return self.f

    def get_color(self, graphics, rgb_list):
        """Helper to convert [R,G,B] from config into a graphics.Color"""
        return graphics.Color(rgb_list[0], rgb_list[1], rgb_list[2])
        
    def reset(self): pass

    def draw_leaderboard(self, canvas, graphics, title, leaders, start_time):
        canvas.Fill(0, 0, 0)
        font = self.get_font(graphics)
        
        # Apply configurable colors
        w = self.get_color(graphics, self.config.color_text)
        g = self.get_color(graphics, self.config.color_rank)
        gold = self.get_color(graphics, self.config.color_title)
        black = graphics.Color(0, 0, 0)
        
        graphics.DrawText(canvas, font, 2, 6, gold, title)

        max_val_len = max(len(str(p['val'])) for p in leaders) if leaders else 3
        stat_x = 64 - (max_val_len * 4) - 1 
        right_mask_start = stat_x - 2
        name_start_x = 12
        visible_name_width = right_mask_start - name_start_x

        y = 14
        for p in leaders:
            name = p['name']
            name_width = len(name) * 4 
            name_x = name_start_x
            
            if name_width > visible_name_width:
                elapsed = time.time() - start_time
                shift = int(elapsed * 8)
                total_scroll = name_width - visible_name_width
                pause = 16 
                cycle = (total_scroll * 2) + (pause * 2) 
                frame = shift % cycle
                
                if frame < pause: offset = 0
                elif frame < pause + total_scroll: offset = frame - pause
                elif frame < (pause * 2) + total_scroll: offset = total_scroll
                else: offset = total_scroll - (frame - (pause * 2) - total_scroll)
                    
                name_x = name_start_x - offset
                
            graphics.DrawText(canvas, font, name_x, y, w, name)
            y += 8
            
        for y_line in range(7, 32):
            graphics.DrawLine(canvas, 0, y_line, name_start_x - 1, y_line, black)
            graphics.DrawLine(canvas, right_mask_start, y_line, 63, y_line, black)
            
        y = 14
        for i, p in enumerate(leaders):
            graphics.DrawText(canvas, font, 2, y, g, f"{i+1}.")
            graphics.DrawText(canvas, font, stat_x, y, g, str(p['val']))
            y += 8

class LastFiveRenderer(BaseRenderer):
    def can_render(self, d): return len(d.last_five) > 0
    def wait_time(self): return 3.0
    def render(self, d, canvas, graphics, pos):
        canvas.Fill(0, 0, 0)
        font = self.get_font(graphics)
        h = self.get_color(graphics, self.config.color_text)
        a = self.get_color(graphics, self.config.color_away)
        
        y = 6
        for g in d.last_five:
            c = a if g['is_away'] else h
            graphics.DrawText(canvas, font, 4, y, c, g['opp'])
            graphics.DrawText(canvas, font, 28, y, c, g['score'])
            graphics.DrawText(canvas, font, 54, y, c, g['res'])
            y += 6
        return None

class NextFiveRenderer(BaseRenderer):
    def can_render(self, d): return len(d.next_five) > 0
    def wait_time(self): return 3.0
    def render(self, d, canvas, graphics, pos):
        canvas.Fill(0, 0, 0)
        font = self.get_font(graphics)
        h = self.get_color(graphics, self.config.color_text)
        a = self.get_color(graphics, self.config.color_away)
        
        y = 6
        for g in d.next_five:
            c = a if g['is_away'] else h
            graphics.DrawText(canvas, font, 1, y, c, g['date'])
            graphics.DrawText(canvas, font, 25, y, c, g['opp'])
            graphics.DrawText(canvas, font, 41, y, c, g['time'])
            y += 6
        return None

class WARRenderer(BaseRenderer):
    def __init__(self, config, layout, colors):
        super().__init__(config, layout, colors)
        self.start_time = 0
        
    def can_render(self, d): return len(d.pos_data) > 0
    def wait_time(self): return 0.04
    def reset(self): self.start_time = 0
    
    def render(self, d, canvas, graphics, pos):
        if self.start_time == 0: self.start_time = time.time()
        
        elapsed = time.time() - self.start_time
        idx = int(elapsed // 6)
        
        if idx >= len(self.config.war_positions): return None 

        curr_pos = self.config.war_positions[idx]
        leaders = d.pos_data.get(curr_pos, [])
        title = f"TOP {curr_pos} (WAR)"
        
        screen_start_time = self.start_time + (idx * 6)
        self.draw_leaderboard(canvas, graphics, title, leaders, screen_start_time)
        return 0

# --- SCROLLING STAT RENDERER ---
class StatRenderer(BaseRenderer):
    def __init__(self, config, layout, colors, metric_key, title):
        super().__init__(config, layout, colors)
        self.metric_key = metric_key
        self.title = title
        self.start_time = 0

    def can_render(self, d): return len(d.leaders.get(self.metric_key, [])) > 0
    def wait_time(self): return 0.04 
    def reset(self): self.start_time = 0

    def render(self, d, canvas, graphics, pos):
        if self.start_time == 0: self.start_time = time.time()
        leaders = d.leaders.get(self.metric_key, [])
        self.draw_leaderboard(canvas, graphics, self.title, leaders, self.start_time)
        return 0

# Subclasses to create the entry points
class HRRenderer(StatRenderer):
    def __init__(self, c, l, col): super().__init__(c, l, col, 'homeRuns', 'MLB HR LEADERS')
class OPSRenderer(StatRenderer):
    def __init__(self, c, l, col): super().__init__(c, l, col, 'onBasePlusSlugging', 'MLB OPS LEADERS')
class AVGRenderer(StatRenderer):
    def __init__(self, c, l, col): super().__init__(c, l, col, 'battingAverage', 'MLB AVG LEADERS')
class RBIRenderer(StatRenderer):
    def __init__(self, c, l, col): super().__init__(c, l, col, 'runsBattedIn', 'MLB RBI LEADERS')
class SBRenderer(StatRenderer):
    def __init__(self, c, l, col): super().__init__(c, l, col, 'stolenBases', 'MLB SB LEADERS')
class ERARenderer(StatRenderer):
    def __init__(self, c, l, col): super().__init__(c, l, col, 'earnedRunAverage', 'MLB ERA LEADERS')
class KRenderer(StatRenderer):
    def __init__(self, c, l, col): super().__init__(c, l, col, 'strikeouts', 'MLB K LEADERS')

# --- EXPORTS ---
def load_last_five(): return (ScheduleConfig, ScheduleData, LastFiveRenderer)
def load_next_five(): return (ScheduleConfig, ScheduleData, NextFiveRenderer)
def load_war_leaders(): return (ScheduleConfig, WARData, WARRenderer)
def load_hr_leaders(): return (ScheduleConfig, StatLeadersData, HRRenderer)
def load_ops_leaders(): return (ScheduleConfig, StatLeadersData, OPSRenderer)
def load_avg_leaders(): return (ScheduleConfig, StatLeadersData, AVGRenderer)
def load_rbi_leaders(): return (ScheduleConfig, StatLeadersData, RBIRenderer)
def load_sb_leaders(): return (ScheduleConfig, StatLeadersData, SBRenderer)
def load_era_leaders(): return (ScheduleConfig, StatLeadersData, ERARenderer)
def load_k_leaders(): return (ScheduleConfig, StatLeadersData, KRenderer)