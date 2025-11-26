"""Check available ballparks."""
from batted_ball.ballpark import list_available_parks, get_ballpark

parks = list_available_parks()
print(f'Available ballparks ({len(parks)}):')
for p in sorted(parks):
    park = get_ballpark(p)
    print(f'  {p:15} - {park.name}')
