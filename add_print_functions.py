"""
Functions to add to SimMetricsCollector in sim_metrics.py

These should be added after _print_batter_summaries and before _print_model_drift_summary
"""

def _print_contact_quality_table(self, team: str):
    """Print contact quality outcome cross-tabulation table"""
    table = self.contact_quality_table_away if team == 'away' else self.contact_quality_table_home

    if not table.buckets:
        return

    print(f"\n📊 CONTACT QUALITY OUTCOME TABLE ({team.upper()} team):")
    print("-" * 100)
    print("Cross-tab of EV/LA buckets with outcomes. Red flags: High EV+optimal LA with no XBH/HR")
    print()

    # Print header
    ev_buckets = ["<70", "70-80", "80-90", "90+"]
    la_buckets = ["<10° (GB)", "10-25° (LD)", "25-35° (HR)", ">35° (Pop)"]

    print(f"{'EV \\ LA':15s}", end="")
    for la in la_buckets:
        print(f" │ {la:18s}", end="")
    print()
    print("─" * 100)

    for ev_bucket in ev_buckets:
        print(f"{ev_bucket:15s}", end="")
        for la_bucket in la_buckets:
            stats = table.get_stats(ev_bucket, la_bucket)
            bip = stats['bip']
            if bip == 0:
                print(f" │ {'--':18s}", end="")
            else:
                hits = stats['hits']
                hr = stats['hr']
                avg = stats['avg']
                slg = stats['slg']
                # Format: "BIP:X H:X HR:X .AVG"
                print(f" │ {bip:2d}BIP {hits:2d}H {hr:2d}HR .{int(avg*1000):03d}", end="")
        print()

    # Check for red flags
    print()
    danger_zone_stats = table.get_stats("90+", "25-35° (HR)")
    if danger_zone_stats['bip'] >= 5 and danger_zone_stats['xbh'] == 0:
        print(f"   ⚠️  RED FLAG: {danger_zone_stats['bip']} BIP in HR zone (90+ EV, 25-35° LA) with 0 XBH!")
    if danger_zone_stats['bip'] >= 10 and danger_zone_stats['hr'] == 0:
        print(f"   ⚠️  RED FLAG: {danger_zone_stats['bip']} BIP in HR zone with 0 HR!")

def _print_sabermetrics(self, team: str):
    """Print basic sabermetric statistics"""
    stats = self.sabermetrics_away if team == 'away' else self.sabermetrics_home

    if stats.at_bats == 0 and stats.hits == 0:
        return

    print(f"\n📈 SABERMETRICS ({team.upper()} team):")
    print("-" * 80)

    avg = stats.get_batting_avg()
    slg = stats.get_slugging()
    iso = stats.get_iso()
    babip = stats.get_babip()
    k_rate = stats.get_k_rate()
    bb_rate = stats.get_bb_rate()

    print(f"   AVG: {avg:.3f}  |  SLG: {slg:.3f}  |  ISO: {iso:.3f}")
    print(f"   BABIP: {babip:.3f}  (MLB ~.290-.300)")
    print(f"   K%: {100*k_rate:.1f}%  |  BB%: {100*bb_rate:.1f}%  (MLB K% ~22%, BB% ~8.5%)")

    # Flag issues
    if babip > 0.360:
        print(f"   ⚠️  BABIP too high: {babip:.3f} (MLB range: .260-.360)")
    elif babip < 0.260 and stats.at_bats > 50:
        print(f"   ⚠️  BABIP too low: {babip:.3f}")

    if iso < 0.100 and stats.at_bats > 50:
        print(f"   ⚠️  ISO very low: {iso:.3f} - lack of power")

    if k_rate > 0.30:
        print(f"   ⚠️  K% too high: {100*k_rate:.1f}%")
    elif k_rate < 0.15 and stats.at_bats > 50:
        print(f"   ⚠️  K% too low: {100*k_rate:.1f}%")

def _print_pitch_type_summaries(self, team: str):
    """Print pitch type usage and effectiveness"""
    summaries = self.pitch_type_summaries_away if team == 'away' else self.pitch_type_summaries_home

    if not summaries:
        return

    print(f"\n🎯 PITCH TYPE SUMMARIES ({team.upper()} pitching staff):")
    print("-" * 100)

    total_pitches = sum(s.count for s in summaries.values())

    # Overall stats first
    total_strikes = sum(s.strikes for s in summaries.values())
    total_swings = sum(s.swings for s in summaries.values())
    total_swstr = sum(s.swinging_strikes for s in summaries.values())
    total_in_zone = sum(s.in_zone for s in summaries.values())
    total_chases = sum(s.out_of_zone_swings for s in summaries.values())

    print(f"   Overall: {total_pitches} pitches")
    print(f"     Strike%: {100*total_strikes/total_pitches:.1f}%  |  SwStr%: {100*total_swstr/total_swings:.1f}% (of swings)  |  Zone%: {100*total_in_zone/total_pitches:.1f}%")
    out_of_zone = total_pitches - total_in_zone
    chase_rate = 100*total_chases/out_of_zone if out_of_zone > 0 else 0
    print(f"     Chase%: {chase_rate:.1f}% (swings at pitches out of zone)")
    print()

    # Per pitch type
    print(f"   {'Type':15s} | {'Usage':6s} | {'Strike%':7s} | {'SwStr%':7s} | {'Velo':8s} | {'Spin':8s} | {'Cmd Err':8s}")
    print("   " + "-" * 85)

    for pitch_type in sorted(summaries.keys(), key=lambda x: summaries[x].count, reverse=True):
        s = summaries[pitch_type]
        usage = 100 * s.count / total_pitches
        strike_rate = 100 * s.get_strike_rate()
        swstr_rate = 100 * s.get_swstr_rate()
        avg_velo = s.get_avg_velocity()
        avg_spin = s.get_avg_spin()
        avg_cmd_err = s.get_avg_command_error()

        print(f"   {pitch_type:15s} | {usage:5.1f}% | {strike_rate:6.1f}% | {swstr_rate:6.1f}% | {avg_velo:6.1f} mph | {avg_spin:6.0f} rpm | {avg_cmd_err:6.2f}\"")

def _print_fielding_timing_stats(self, team: str):
    """Print fielding timing margin statistics"""
    timing = self.fielding_timing_away if team == 'away' else self.fielding_timing_home

    if not timing.buckets or all(b['bip'] == 0 for b in timing.buckets.values()):
        return

    print(f"\n🧤 FIELDING TIMING DIAGNOSTICS ({team.upper()} defense):")
    print("-" * 80)
    print("Plays bucketed by timing margin (fielder arrival - ball arrival)")
    print()

    print(f"   {'Margin':12s} | {'BIP':4s} | {'Outs':5s} | {'Hits':5s} | {'Out%':6s}")
    print("   " + "-" * 50)

    for bucket in ['<0s', '0-0.5s', '0.5-1.0s', '1.0-2.0s', '>2.0s']:
        data = timing.buckets[bucket]
        bip = data['bip']
        if bip == 0:
            continue
        outs = data['outs']
        hits = data['hits']
        out_pct = 100 * outs / bip if bip > 0 else 0

        print(f"   {bucket:12s} | {bip:4d} | {outs:5d} | {hits:5d} | {out_pct:5.1f}%")

    # Red flags
    negative_margin_plays = timing.buckets['<0s']
    if negative_margin_plays['bip'] > 0 and negative_margin_plays['outs'] > 0:
        print(f"\n   ⚠️  {negative_margin_plays['outs']} outs recorded with negative margin (<0s) - check diving catch logic")

    # Error breakdown
    if timing.errors_by_position:
        print(f"\n   Errors by position:")
        for pos, count in sorted(timing.errors_by_position.items(), key=lambda x: x[1], reverse=True):
            print(f"     {pos}: {count}")

def _print_sanity_check_flags(self):
    """Print automatic model sanity check flags"""
    print(f"\n🚨 MODEL SANITY CHECKS:")
    print("-" * 80)

    flags_found = False

    # Check HR/FB rate
    fly_balls = [b for b in self.batted_ball_metrics if b.hit_type == 'fly_ball']
    if len(fly_balls) >= 20:
        home_runs = sum(1 for b in fly_balls if b.actual_outcome == 'home_run')
        hr_fb_rate = 100 * home_runs / len(fly_balls) if len(fly_balls) > 0 else 0
        if hr_fb_rate < 1.0:
            print(f"   ⚠️  HR/FB rate too low: {hr_fb_rate:.1f}% (MLB ~12-14%)")
            flags_found = True
        elif hr_fb_rate > 20.0:
            print(f"   ⚠️  HR/FB rate too high: {hr_fb_rate:.1f}% (MLB ~12-14%)")
            flags_found = True

    # Check BABIP
    for team in ['away', 'home']:
        stats = self.sabermetrics_away if team == 'away' else self.sabermetrics_home
        if stats.at_bats >= 50:
            babip = stats.get_babip()
            if babip > 0.360:
                print(f"   ⚠️  {team.upper()} BABIP out-of-range: {babip:.3f} (MLB range: .260-.360)")
                flags_found = True
            elif babip < 0.260:
                print(f"   ⚠️  {team.upper()} BABIP out-of-range: {babip:.3f} (MLB range: .260-.360)")
                flags_found = True

    # Check average EV
    if len(self.batted_ball_metrics) >= 20:
        avg_ev = np.mean([b.exit_velocity_mph for b in self.batted_ball_metrics])
        if avg_ev < 84.0:
            print(f"   ⚠️  Average exit velocity depressed: {avg_ev:.1f} mph (MLB ~88 mph)")
            flags_found = True

    # Check LA bucket sum
    gbs = sum(1 for b in self.batted_ball_metrics if b.hit_type == 'ground_ball')
    lds = sum(1 for b in self.batted_ball_metrics if b.hit_type == 'line_drive')
    fbs = sum(1 for b in self.batted_ball_metrics if b.hit_type == 'fly_ball')
    pops = sum(1 for b in self.batted_ball_metrics if b.hit_type == 'popup')
    total_bip = len(self.batted_ball_metrics)
    classified = gbs + lds + fbs + pops
    if total_bip > 0 and abs(classified - total_bip) > 0:
        print(f"   ⚠️  Hit type classification mismatch: {classified} classified vs {total_bip} total")
        flags_found = True

    # Check error rate (errors tracked in fielding timing stats)
    total_errors = sum(self.fielding_timing_away.errors_by_position.values())
    total_errors += sum(self.fielding_timing_home.errors_by_position.values())
    if len(self.fielding_metrics) > 0:
        error_rate = total_errors / len(self.fielding_metrics)
        if error_rate > 0.10:  # More than 10% error rate
            print(f"   ⚠️  Error rate too high: {100*error_rate:.1f}% ({total_errors} errors in {len(self.fielding_metrics)} plays)")
            flags_found = True

    if not flags_found:
        print("   ✓ No major issues detected")

def _print_series_scoreboard(self):
    """Print series-level scoreboard and run distributions"""
    if not self.series_scoreboard.game_results:
        return

    print(f"\n🏆 SERIES SCOREBOARD:")
    print("-" * 80)

    for game in self.series_scoreboard.game_results:
        away_score = game['away_score']
        home_score = game['home_score']
        notes = game.get('notes', '')
        winner = "Away" if away_score > home_score else "Home" if home_score > away_score else "Tie"

        print(f"   G{game['game_num']}: Away {away_score} @ Home {home_score}  [{winner}] {notes}")

    # Run distributions
    print(f"\n   Run Distribution (Away):")
    for runs in sorted(self.series_scoreboard.away_runs_distribution.keys()):
        count = self.series_scoreboard.away_runs_distribution[runs]
        bar = "█" * count
        print(f"     {runs} runs: {bar} ({count} games)")

    print(f"\n   Run Distribution (Home):")
    for runs in sorted(self.series_scoreboard.home_runs_distribution.keys()):
        count = self.series_scoreboard.home_runs_distribution[runs]
        bar = "█" * count
        print(f"     {runs} runs: {bar} ({count} games)")

    # Margin of victory
    print(f"\n   Margin of Victory:")
    for margin in sorted(self.series_scoreboard.margin_distribution.keys()):
        count = self.series_scoreboard.margin_distribution[margin]
        bar = "█" * count
        print(f"     {margin} run(s): {bar} ({count} games)")

def _print_sim_config(self):
    """Print simulation configuration for reproducibility"""
    print(f"\n⚙️  SIMULATION CONFIGURATION:")
    print("-" * 80)

    cfg = self.sim_config
    print(f"   Engine version: {cfg.engine_version}")
    if cfg.git_commit:
        print(f"   Git commit: {cfg.git_commit}")
    if cfg.rng_seed is not None:
        print(f"   RNG seed: {cfg.rng_seed}")

    print(f"\n   Park Settings:")
    print(f"     Name: {cfg.park_name}")
    print(f"     Altitude: {cfg.park_altitude:.0f} ft")
    if cfg.park_dimensions:
        print(f"     Dimensions: {cfg.park_dimensions}")

    print(f"\n   Weather:")
    print(f"     Temperature: {cfg.temperature:.1f}°F")
    print(f"     Wind: {cfg.wind_speed:.1f} mph @ {cfg.wind_direction:.0f}°")

    if cfg.tuning_multipliers:
        print(f"\n   Tuning Multipliers:")
        for key, val in cfg.tuning_multipliers.items():
            print(f"     {key}: {val:.2f}x")
