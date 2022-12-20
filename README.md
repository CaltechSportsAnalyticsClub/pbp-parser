Todo: 

- Write tests
- Clean up code
  - I'm sure we can make this a lot faster (a game takes like 10 seconds right now, because the best way I could find how to do it is to make like 5 requests to the NBA API)
  - [https://github.com/rd11490/NBA-Play-By-Play-Example](this) is how I am doing it currently, with some additional logic. 
  
- Run batches of games at a time (Threadpool so that we're not too slow, but not too fast that we get rate limited)

To download:

```
git clone https://github.com/CaltechSportsAnalyticsClub/pbp-parser.git
pip install -e pbp-parser
```

I'll make it so that you don't need to install from source once I get to cleaning everything up. 

Usage

```
from pbp_parser import parser
pbp = parser.PlayByPlay(game_id="0022200413")
pbp.pbp_df
```
