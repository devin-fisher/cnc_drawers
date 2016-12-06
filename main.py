from prompt import prompt, prompt_num
from mecode import G

SAFETY_HEIGHT = 0.5
OVER_LAP_FACTOR = 0.8

DEFAULT_GROOVE_BIT = .25
#  Drawing not to scale
#  (for visualizing)
#        /\
#  _ _ _/  \
# |         |_ _
# |             |
# |             |
# |_ _ _ _ _ _ _|

OUTER_CUT_WIDTH_FACTOR  = 1.5
INNER_CUT_WIDTH_FACTOR = 0.75

OUTER_CUT_DEPTH_FACTOR  = -0.5
INNER_CUT_DEPTH_FACTOR = -0.75


def _valid_units(answer):
    if answer in ['inch', 'cm']:
        return answer
    else:
        raise Exception("'%s' is not a valid Unit Type" % answer)


def define_channel(g, channel, axis, x_start, y_start, length, orientation, bit_diameter):
    total_movement = length
    over_lap = bit_diameter*OVER_LAP_FACTOR
    half_bit_dia = bit_diameter/2.0
    # Get read to cut
    g.move(z=SAFETY_HEIGHT)

    adjusted_x_start = x_start
    adjusted_y_start = y_start

    # bit adjustment
    if axis == 'X':
        adjusted_x_start += half_bit_dia
    elif axis == 'Y':
        adjusted_y_start += half_bit_dia

    g.move(x=adjusted_x_start, y=adjusted_y_start)

    # Wide Channel
    g.move(z=channel['wide_channel']['depth'])
    if axis == 'X':
        g.meander(channel['wide_channel']['width'] - half_bit_dia, total_movement, over_lap, orientation='y')
    elif axis == 'Y':
        g.meander(total_movement, channel['wide_channel']['width'] - half_bit_dia, over_lap, orientation='x')

    g.move(z=SAFETY_HEIGHT)


    # Narrow Channel
    if orientation == 'RIGHT':
        if axis == 'X':
            adjusted_x_start = x_start + half_bit_dia + (channel['wide_channel']['width'] - channel['narrow_channel']['width'])
        elif axis == 'Y':
            adjusted_y_start = y_start + half_bit_dia + (channel['wide_channel']['width'] - channel['narrow_channel']['width'])

    g.move(x=adjusted_x_start, y=adjusted_y_start)
    g.move(z=channel['narrow_channel']['depth'])
    if axis == 'X':
        g.meander(channel['narrow_channel']['width'] - half_bit_dia, total_movement, over_lap, orientation='y')
    elif axis == 'Y':
        g.meander(total_movement, channel['narrow_channel']['width'] - half_bit_dia, over_lap, orientation='x')

    # Done cutting
    g.move(z=SAFETY_HEIGHT)


def define_channels(g, channel, layout, step_down, tool_diameter):
    non_factor_axis = 0

    x_cut_length = layout['x_cut_length']
    y_cut_length = layout['y_cut_length']

    #tool zero
    g.write("T0 M06")

    define_channel(g, channel, 'X', 0, 0, 5, 'RIGHT', .25)

    # x cuts
    # define_channel(g, channel, 'X', layout['x_channel_1'], non_factor_axis, x_cut_length, 'RIGHT', tool_diameter)
    # define_channel(g, channel, 'X', layout['x_channel_2'], non_factor_axis, x_cut_length, 'LEFT', tool_diameter)

    # y cuts
    # define_channel(g, channel, 'Y', non_factor_axis, layout['y_channel_1'], y_cut_length, 'RIGHT', tool_diameter)
    # define_channel(g, channel, 'Y', non_factor_axis, layout['y_channel_2'], y_cut_length, 'LEFT', tool_diameter)


def cal_lateral_movement(value, channel, orientation):
    if orientation == 'RIGHT':
        return value + (channel['wide_channel']['width'] - channel['groove']['mid_point'])
    elif orientation == 'LEFT':
        return value + channel['groove']['mid_point']


def define_vgroove(g, channel, axis, x_start, y_start, length, orientation):
    g.move(z=SAFETY_HEIGHT)
    if axis == 'X':
        x_val = cal_lateral_movement(x_start, channel, orientation)
        y_val = y_start
    elif axis == 'Y':
        x_val = x_start
        y_val = cal_lateral_movement(y_start, channel, orientation)

    g.move(x=x_val, y=y_val)
    g.write("T1 M06")
    g.move(z=-channel['groove']['depth'])
    if axis == 'X':
        g.move(y=length)
        pass
    elif axis == 'Y':
        g.move(x=length)

    # Done cutting
    g.move(z=SAFETY_HEIGHT)


def define_vgrooves(g, channel, layout):
    non_factor_axis = 0

    x_cut_length = layout['x_cut_length']
    y_cut_length = layout['y_cut_length']

    # tool one
    g.write("T1 M06")
    define_vgroove(g, channel, 'X', 0, 0, 5, 'RIGHT')

    # # x cuts
    # define_vgroove(g, channel, 'X', layout['x_channel_1'], non_factor_axis, x_cut_length, 'RIGHT')
    # define_vgroove(g, channel, 'X', layout['x_channel_2'], non_factor_axis, x_cut_length, 'LEFT')
    #
    # # y cuts
    # define_vgroove(g, channel, 'Y', non_factor_axis, layout['y_channel_1'], y_cut_length, 'RIGHT')
    # define_vgroove(g, channel, 'Y', non_factor_axis, layout['y_channel_2'], y_cut_length, 'LEFT')


def cal_layout(x_width, y_width, side_height, wide_channel_width):
    rtn = dict()
    rtn['non_factor_axis'] = 0

    rtn['x_channel_1'] = side_height
    rtn['x_channel_2'] = side_height + wide_channel_width + x_width
    rtn['y_channel_1'] = side_height
    rtn['y_channel_2'] = side_height + wide_channel_width + y_width

    rtn['x_cut_length'] = 2 * side_height + 2 * wide_channel_width + y_width
    rtn['y_cut_length'] = 2 * side_height + 2 * wide_channel_width + x_width
    return rtn


def cal_channel(depth, groove_bit_size=DEFAULT_GROOVE_BIT):
    if depth > 0:
        depth *= -1

    vd = groove_depth = groove_bit_size/2.0
    cd = channel_depth = abs(depth) - vd

    rtn = dict()
    rtn['wide_channel'] = {
        'width': (cd + 2.0*vd + cd/2.0),
        'depth': -(cd/2.0)
    }

    rtn['narrow_channel'] = {
        'width': (2.0*vd + cd/2.0),
        'depth': -cd
    }

    rtn['groove'] = {
        'mid_point': rtn['narrow_channel']['width'] - vd,
        'depth': -depth
    }
    return rtn

def main():
    # unit = prompt('Unit Type - inch or mm', defaultValue="inch", normfunc=_valid_units, retry=True)
    # unit_plural = unit+"s"
    # x_width = prompt_num('Base length in %s' % unit_plural, retry=True)
    # y_width = prompt_num('Base width in %s' % unit_plural, retry=True)
    # side_height = prompt_num('Side height in %s' % unit_plural, retry=True)
    # depth = prompt_num('Stock depth in %s' % unit_plural, retry=True)

    x_width = 10
    y_width = 10
    side_height = 15
    depth = .5
    cylindrical_mill_diameter = .5
    step_down = .25

    # TODO Should check that parameters can work especially bit size

    channel = cal_channel(depth)
    print channel

    layout = cal_layout(x_width, y_width, side_height, channel['wide_channel']['width'])
    print layout

    with G(direct_write=False, header=None, setup=False, print_lines=True) as g:
        # header
        g.write("G20 G90 G40")

        g.absolute()
        g.setup()

        g.feed(30)
        define_channels(g, channel, layout, step_down, cylindrical_mill_diameter)
        define_vgrooves(g, channel, layout)

        # end
        g.move(z=SAFETY_HEIGHT)
        g.move(x=0, y=0)

        view(g)


def view(g):
    import numpy as np
    history = np.array(g.position_history)

    from mpl_toolkits.mplot3d import Axes3D
    import matplotlib.pyplot as plt
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    ax.set_aspect('equal')
    X, Y, Z = history[:, 0], history[:, 1], history[:, 2]
    ax.plot(X, Y, Z)
    ax.set_xlabel('X', fontsize=18)
    ax.set_ylabel('Y', fontsize=18)
    ax.set_zlabel('Z', fontsize=18)
    # plt.zlabel('Z', fontsize=18)

    # Hack to keep 3D plot's aspect ratio square. See SO answer:
    # http://stackoverflow.com/questions/13685386
    max_range = np.array([X.max()-X.min(),
                          Y.max()-Y.min(),
                          Z.max()-Z.min()]).max() / 2.0

    mean_x = X.mean()
    mean_y = Y.mean()
    mean_z = Z.mean()
    ax.set_xlim(mean_x - max_range, mean_x + max_range)
    ax.set_ylim(mean_y - max_range, mean_y + max_range)
    ax.set_zlim(mean_z - max_range, mean_z + max_range)

    plt.show()


def inkscape_points(channel):
    print "inkscape coord"
    print "(0,0)"
    print "(%s,%s)" % ("0", str(abs(channel['narrow_channel']['depth'])))
    print "(%s,%s)" % (str(channel['narrow_channel']['width'] - DEFAULT_GROOVE_BIT), str(abs(channel['narrow_channel']['depth'])))
    print "(%s,%s)" % (abs(channel['groove']['mid_point']), abs(channel['groove']['depth']))
    print "(%s,%s)" % (str(channel['narrow_channel']['width']), str(abs(channel['narrow_channel']['depth'])))
    print "(%s,%s)" % (str(channel['narrow_channel']['width']), str(abs(channel['wide_channel']['depth'])))
    print "(%s,%s)" % (str(channel['wide_channel']['width']), str(abs(channel['wide_channel']['depth'])))
    print "(%s,%s)" % (str(channel['wide_channel']['width']), "0")

if __name__ == '__main__':
    main()
