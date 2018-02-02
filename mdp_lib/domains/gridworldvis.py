from __future__ import division
from itertools import product

import numpy as np

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Arrow, Circle
from matplotlib.path import Path
import matplotlib.patheffects as path_effects
import matplotlib.patches as patches
import matplotlib.animation as animation

# ================================#
#
#	Visualization stuff
#
# ================================#

def visualize_states(ax=None, states=None,
                     tile_color=None,
                     plot_size=None,
                     panels=None,
                     **kwargs):
    '''
        Supported kwargs:
            - tile_color : a dictionary from tiles (states) to colors
            - plot_size is an integer specifying how many tiles wide
              and high the plot is, with the grid itself in the middle
    '''
    if tile_color is None:
        tile_color = {}

    if ax == None:
        fig = plt.figure()
        ax = fig.add_subplot(111)

    if panels is None:
        panels = []

    # plot squares
    for s in states:
        if s == (-1, -1):
            continue
        square = Rectangle(s, 1, 1, color=tile_color.get(s, 'white'), ec='k',
                           lw=2)
        ax.add_patch(square)

    ax.axis('off')
    if plot_size is None and len(panels) == 0:
        ax.set_xlim(-0.1, 1 + max([s[0] for s in states]) + .1)
        ax.set_ylim(-0.1, 1 + max([s[1] for s in states]) + .1)
        ax.axis('scaled')
    elif len(panels) > 0:
        xlim = [-0.1, 1 + max([s[0] for s in states]) + .1]
        ylim = [-0.1, 1 + max([s[1] for s in states]) + .1]
        if 'right' in panels:
            xlim[1] += 2
        if 'left' in panels:
            xlim[0] -= 2
        if 'top' in panels:
            ylim[1] += 2
        if 'bottom' in panels:
            ylim[0] -= 2
        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
    else:
        cx = (max([s[0] for s in states])+1)/2
        cy = (max([s[1] for s in states])+1)/2
        ax.set_xlim(cx-0.1-plot_size/2, cx+0.1+plot_size/2)
        ax.set_ylim(cy-0.1-plot_size/2, cy+0.1+plot_size/2)
    return ax



def visualize_deterministic_policy(ax, policy, absorbing_action='%', **kwargs):
    policy = dict([(s, {a: 1.0}) for s, a in policy.iteritems() if
                   a != absorbing_action])
    return visualize_action_values(ax, policy, **kwargs)


def visualize_action_values(ax=None, state_action_values=None,
                            color_valence=False,
                            global_maxval=None,
                            arrowwidth=.1,
                            **kwargs):
    '''
        Supported kwargs:
            - color_valence : boolean whether to color negative red and positive blue, otherwise color is always black
            - global_maxval : max value to normalize arrow lengths to
    '''

    # plot arrows
    if global_maxval is None:
        global_maxval = -np.inf
        for s, a_v in state_action_values.iteritems():
            for v in a_v.values():
                if global_maxval < np.absolute(v):
                    global_maxval = np.absolute(v)

    for s, a_v in state_action_values.iteritems():
        if s == (-1, -1):
            continue
        x, y = s
        normalization = np.sum(np.absolute(a_v.values()))
        maxval = max(np.absolute(a_v.values()))
        for a, v in a_v.iteritems():
            if a == '%' or v == 0:
                continue

            mag = (.5 / global_maxval) * np.absolute(v)

            if color_valence:
                if v <= 0:
                    arrowColor = 'red'
                else:
                    arrowColor = 'blue'
            else:
                arrowColor = 'k'
            if a == '<':
                ax.add_patch(Arrow(x + .5, y + .5, -mag, 0, width=arrowwidth,
                                   color=arrowColor))
            elif a == '>':
                ax.add_patch(Arrow(x + .5, y + .5, mag, 0, width=arrowwidth,
                                   color=arrowColor))
            elif a == 'v':
                ax.add_patch(Arrow(x + .5, y + .5, 0, -mag, width=arrowwidth,
                                   color=arrowColor))
            elif a == '^':
                ax.add_patch(Arrow(x + .5, y + .5, 0, mag, width=arrowwidth,
                                   color=arrowColor))
            elif a == 'x':
                ax.add_patch(
                    Circle((x + .5, y + .5), radius=mag * .9, fill=False))
            else:
                raise Exception('unknown action')
    return ax


def visualize_trajectory(axis=None, traj=None,
                         jitter_mean=0,
                         jitter_var=.1,
                         plot_actions=False,
                         endpoint_jitter=False,
                         color='black',
                         outline=False,
                         outline_color='white',
                         lw=1,
                         **kwargs):

    traj = [(t[0], t[1]) for t in traj] #traj only depends on state actions

    if len(traj) == 2:
        p0 = tuple(np.array(traj[0][0]) + .5)
        p2 = tuple(np.array(traj[1][0]) + .5)
        p1 = np.array([(p0[0] + p2[0]) / 2, (p0[1] + p2[1]) / 2]) \
                        + np.random.normal(0, jitter_var, 2)
        if endpoint_jitter:
            p0 = tuple(
                np.array(p0) + np.random.normal(jitter_mean, jitter_var, 2))
            p1 = tuple(
                np.array(p1) + np.random.normal(jitter_mean, jitter_var, 2))
        segments = [[p0, p1, p2], ]
    elif (len(traj) == 3) and (traj[0][0] == traj[2][0]):
        p0 = tuple(np.array(traj[0][0]) + .5)
        p2 = tuple(np.array(traj[1][0]) + .5)
        if abs(p0[0] - p2[0]) > 0:  # horizontal
            jitter = np.array(
                [0, np.random.normal(jitter_mean, jitter_var * 2)])
            p2 = p2 - np.array([.25, 0])
        else:  # vertical
            jitter = np.array(
                [np.random.normal(jitter_mean, jitter_var * 2), 0])
            p2 = p2 - np.array([0, .25])
        p1 = p2 + jitter
        p3 = p2 - jitter
        segments = [[p0, p1, p2], [p2, p3, p0]]
    else:
        state_coords = []
        for s, a in traj:
            jitter = np.random.normal(jitter_mean, jitter_var, 2)
            coord = np.array(s) + .5 + jitter
            state_coords.append(tuple(coord))
        if not endpoint_jitter:
            state_coords[0] = tuple(np.array(traj[0][0]) + .5)
            state_coords[-1] = tuple(np.array(traj[-1][0]) + .5)
        join_point = state_coords[0]
        segments = []
        for i, s in enumerate(state_coords[:-1]):
            ns = state_coords[i + 1]

            segment = []
            segment.append(join_point)
            segment.append(s)
            if i < len(traj) - 2:
                join_point = tuple(np.mean([s, ns], axis=0))
                segment.append(join_point)
            else:
                segment.append(ns)
            segments.append(segment)

    outline_patches = []
    if outline:
        for segment, step in zip(segments, traj[:-1]):
            codes = [Path.MOVETO, Path.CURVE3, Path.CURVE3]
            path = Path(segment, codes)
            outline_patch = patches.PathPatch(path, facecolor='none',
                                              capstyle='butt',
                                              edgecolor=outline_color, lw=lw*2)
            if axis is not None:
                axis.add_patch(outline_patch)
            outline_patches.append(outline_patch)

    traj_patches = []
    action_patches = []
    for segment, step in zip(segments, traj[:-1]):
        state = step[0]
        action = step[1]

        codes = [Path.MOVETO, Path.CURVE3, Path.CURVE3]
        path = Path(segment, codes)

        patch = patches.PathPatch(path, facecolor='none', capstyle='butt',
                                  edgecolor=color, lw=lw, **kwargs)
        traj_patches.append(patch)
        if axis is not None:
            axis.add_patch(patch)

        if plot_actions:
            dx = 0
            dy = 0
            if action == '>':
                dx = 1
            elif action == 'v':
                dy = -1
            elif action == '^':
                dy = 1
            elif action == '<':
                dx = -1
            action_arrow = patches.Arrow(segment[1][0], segment[1][1],
                                         dx*.4,
                                         dy*.4,
                                         width=.25,
                                         color='grey')
            action_patches.append(action_arrow)
            if axis is not None:
                axis.add_patch(action_arrow)
    return {
        'outline_patches': outline_patches,
        'traj_patches': traj_patches,
        'action_patches': action_patches
    }


def plot_point(axis, state, point_format='bx', **kwargs):
    axis.plot(state[0] + .5, state[1] + .5, point_format, **kwargs)


def plot_text(axis, state, text, outline=False, outline_linewidth=1,
              outline_color='black',
              x_offset=0, y_offset=0,
              mytext=None,
              **kwargs):
    mytext = axis.text(state[0] + .5 + x_offset, state[1] + .5 + y_offset,
                       text, **kwargs)
    if outline:
        mytext.set_path_effects([path_effects.Stroke(
            linewidth=outline_linewidth, foreground=outline_color),
                                 path_effects.Normal()])
    return mytext

def visualize_walls(ax=None, walls=None, wall_styles=None, wall_width=.13):
    if ax is None:
        fig = plt.figure()
        ax = fig.add_subplot(111)
    if wall_styles is None:
        wall_styles = {}

    for s, side in walls:
        x, y = s
        kwargs = {'color': 'black',
                  'fill': True,
                  'lw': 0}
        kwargs.update(wall_styles.get((s, side), {}))
        if side == '^':
            w = Rectangle((x, y+1 - wall_width), 1, wall_width, **kwargs)
        elif side == 'v':
            w = Rectangle((x, y), 1, wall_width, **kwargs)
        elif side == '<':
            w = Rectangle((x, y), wall_width, 1, **kwargs)
        elif side == '>':
            w = Rectangle((x + 1 - wall_width, y), wall_width, 1, **kwargs)
        ax.add_patch(w)
    return ax

def visualize_intervention_trajectory(axis, traj, absorbing_states,
                                      show_intervention_counts=True,
                                      show_agent_moves=True,
                                      show_interventions=True,
                                      plot_post_absorbing_state=True,
                                      agent_move_kwargs=None,
                                      intervention_kwargs=None
                                      ):
    '''
    traj format is [(s, a, ns, intervention), ...]
    '''
    if agent_move_kwargs is None:
        agent_move_kwargs = {}
    if intervention_kwargs is None:
        intervention_kwargs = {}

    agent_move_defaults = {'linewidth': 2}
    for k, v in agent_move_defaults.iteritems():
        if k not in agent_move_kwargs:
            agent_move_kwargs[k] = v

    intervention_kwargs_defaults = {'color': 'red', 'linewidth': 1}
    for k, v in intervention_kwargs_defaults.iteritems():
        if k not in intervention_kwargs:
            intervention_kwargs[k] = v

    # segmenting
    traj_segments = []
    traj_segment = []
    for ti, t in enumerate(traj):
        traj_segment.append(t[:2])
        if (t[-1] is not None) and (t[3] != t[2]):
            traj_segment.append((t[2], '*'))

            traj_segments.append(traj_segment)
            if t[3] in absorbing_states:
                traj_segments.append([(t[3], '%'), ])
            elif (ti == (len(traj) - 1)):
                traj_segments.append([(t[3], '%'), ])
            elif t[2] in absorbing_states:
                traj_segments.append([(t[2], '%'), ])
                if not plot_post_absorbing_state:
                    break
            traj_segment = []
        elif t[2] in absorbing_states:
            traj_segment.append((t[2], '%'))
            traj_segments.append(traj_segment)

    # plotting episode
    last_segment = None
    intervention_count = 1
    intervention_labels = {}
    for traj_segment in traj_segments:
        if len(traj_segment) > 1:
            if show_agent_moves:
                visualize_trajectory(axis, traj_segment, **agent_move_kwargs)
        if last_segment == None:
            last_segment = traj_segment
            continue
        if last_segment[-1] == traj_segment[0]:
            continue

        if show_interventions:
            visualize_trajectory(axis, [last_segment[-1], traj_segment[0]],
                                 jitter_var=.25, jitter_mean=.25,
                                 **intervention_kwargs
                                 )
            plot_point(axis, last_segment[-1][0], 'ro')
            plot_point(axis, traj_segment[0][0], 'r*', markersize=15)

        intervention_labels[last_segment[-1][0]] = intervention_labels.get(
            last_segment[-1][0], [])
        intervention_labels[last_segment[-1][0]].append(
            str(intervention_count))
        intervention_count += 1
        last_segment = traj_segment

    if show_intervention_counts:
        for s, labels in intervention_labels.iteritems():
            plot_text(axis, s, ', '.join(labels), color='yellow', ha='center',
                      va='top',
                      size=25, outline=True, x_offset=-.1, y_offset=-.1)

def plot_agent_location(state, next_state=None,
                        agent=None,
                        interpolation=0,
                        tween_function="easeInOutExpo",
                        ax=None,
                        zorder=10):
    if next_state in [(-1, -1), (-2, -2)]:
        next_state = None

    import pytweening

    interpolation = getattr(pytweening, tween_function)(interpolation)

    if next_state is None or interpolation == 0:
        dstate = state
    else:
        dstate = (state[0] + (next_state[0] - state[0]) * interpolation,
                  state[1] + (next_state[1] - state[1]) * interpolation)

    if agent is None:
        agent = plt.Circle((dstate[0] + .5, dstate[1] + .5), .3,
                           facecolor='b', edgecolor='w',
                           lw=2, zorder=zorder)
    else:
        agent.center = (dstate[0] + .5, dstate[1] + .5)

    #hide if its in a terminal state
    if state in [(-1, -1), (-2, -2)]:
        agent.set_alpha(0.0)
    elif agent._alpha == 0.0:
        agent.set_alpha(1.0)

    ax.add_artist(agent)
    return agent

def animate_trajectory(gw, traj, filename,
                       move_interval=1000,
                       interval_frames=1,
                       traj_responsetimes=None,
                       fig=None,
                       plot_traj_path=True,
                       plot_agent=True,
                       easing='easeInOutExpo',
                       traj_easings=None,
                       init_traj_annotations=None,
                       traj_annotations=None,

                       #gridworld plot parameters
                       feature_colors=None,
                       annotations=None
                      ):
    if fig is None:
        fig = plt.figure()
    ax = fig.add_subplot(111)

    artists = {'agent': None}

    if init_traj_annotations is None:
        init_traj_annotations = {}
    artists.update(init_traj_annotations)

    def init_anim():
        gw.plot(ax=ax,
                feature_colors=feature_colors,
                annotations=annotations)
        return []

    def animate(step):
        if step is None:
            return []

        traj_step, interval_frame = step
        state = traj[traj_step][0]

        step_easing = easing #default easing

        if traj_step < (len(traj) - 1):
            next_state = traj[traj_step + 1][0]

            #handle easings
            if traj_easings is not None:
                step_easing = traj_easings[traj_step]
        else:
            next_state = None



        interpolation=interval_frame/interval_frames
        agent = artists['agent']
        agent = plot_agent_location(
            state=state,
            next_state=next_state,
            agent=agent,
            interpolation=interpolation,
            ax=ax,
            tween_function=step_easing
        )
        artists['agent'] = agent
        return [agent,]

    if traj_responsetimes is None:
        traj_responsetimes = [0,]*len(traj)

    interval = move_interval/interval_frames

    frames = []
    for step_i, frame_i in product(range(len(traj)), range(interval_frames)):
        frames.append((step_i, frame_i))
        if frame_i == 0:
            n_wait_frames = int(traj_responsetimes[step_i]/interval)
            frames.extend([None,]*n_wait_frames)

    ani = animation.FuncAnimation(fig=fig,
                                  func=animate,
                                  init_func=init_anim,
                                  frames=frames,
                                  interval=interval,
                                  blit=True
                                 )
    ani.save(filename)
    return ani