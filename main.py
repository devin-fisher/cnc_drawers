from prompt import prompt, prompt_num
from mecode import G

SAFETY_HEIGHT = 0.5
OVER_LAP_FACTOR = 0.8
#  Drawing not to scale
#  (for visualizing)
#        /\
#  _ _ _/  \
# |         |_ _
# |             |
# |             |
# |_ _ _ _ _ _ _|

OUTER_CUT_WIDTH_FACTOR  = 1.5
INNNER_CUT_WIDTH_FACTOR = 0.75

OUTER_CUT_DEPTH_FACTOR  = -0.5
INNNER_CUT_DEPTH_FACTOR = -0.75

cut_def = {}

def _valid_units(answer):
    if answer in ['inch', 'cm']:
        return answer
    else:
        raise Exception("'%s' is not a valid Unit Type"% answer)

def define_flat_cut(g, x_start, y_start, total_movement, par_axis, pos):

    #get read to cut
    g.move(z=SAFETY_HEIGHT)
    g.move(x=x_start, y=y_start)

    #large pocket
    if par_axis == 'x':
        if pos == "TOP":
            out_meander_start = 'UL'
        else:
            out_meander_start = 'LL'

    if par_axis == 'y':
        if pos == "TOP":
            out_meander_start = 'LR'
        else:
            out_meander_start = 'LL'


    g.move(z=cut_def['out_depth'])
    if par_axis=='x':
        g.meander(total_movement, cut_def['out_cut'], cut_def['over_lap'], start=out_meander_start, orientation=par_axis)
    else:
        g.meander(cut_def['out_cut'], total_movement, cut_def['over_lap'], start=out_meander_start, orientation=par_axis)

    #small pocket

    if par_axis == 'x':
        if pos == "TOP":
            inner_meander_start = 'L'
        else:
            inner_meander_start = 'U'

        if(g.current_position[par_axis] < 0):
            inner_meander_start = inner_meander_start+'L'
        else:
            inner_meander_start = inner_meander_start+'L'

    if par_axis == 'y':
        if(g.current_position[par_axis] < 0):
            inner_meander_start = 'L'
        else:
            inner_meander_start = 'U'

        if pos == "TOP":
            inner_meander_start = inner_meander_start + 'L'
        else:
            inner_meander_start = inner_meander_start + 'R'

    g.move(z=cut_def['inner_depth'])

    if par_axis=='x':
        g.meander(total_movement, cut_def['inner_cut'], cut_def['over_lap'], start=inner_meander_start, orientation=par_axis)
    else:
        g.meander(cut_def['inner_cut'], total_movement, cut_def['over_lap'], start=inner_meander_start, orientation=par_axis)

    #done cutting
    g.move(z=SAFETY_HEIGHT)

def define_flat_cuts(g, length, width, height, depth, cylindrical_mill_diameter):
    cut_start = -0.1-cylindrical_mill_diameter

    #tool zero
    g.write("T0 M06")

    # x cuts
    define_flat_cut(g, cut_start, height+cut_def['tool_half_diameter'], cut_def['x_movement'], 'x', "BOT")
    define_flat_cut(g, cut_start, height + cut_def['cut_width'] + width + (cut_def['cut_width'] - cut_def['tool_half_diameter']), cut_def['x_movement'], 'x', "TOP")

    # y cuts
    define_flat_cut(g, height + cut_def['tool_half_diameter'], cut_start, cut_def['y_movement'], 'y', "BOT")
    define_flat_cut(g, height + cut_def['cut_width'] + length + (cut_def['cut_width'] - cut_def['tool_half_diameter']), cut_start, cut_def['y_movement'], 'y', "TOP")

def define_conical_cut(g, x_start, y_start, total_movement, conical_mill_diameter, par_axis):
    g.move(z=.5)
    g.move(x=x_start, y=y_start)
    g.write("T1 M06")
    g.move(z=-1*cut_def['full_depth'])
    if par_axis == 'x':
        g.move(x=total_movement)
    else:
        g.move(y=total_movement)

def define_conical_cuts(g, length, width, height, depth, conical_mill_diameter):
    cut_start = -0.1-conical_mill_diameter
    #tool one
    g.write("T1 M06")

    # x cuts
    define_conical_cut(g, cut_start, height + depth, cut_def['x_movement'], conical_mill_diameter, 'x')
    define_conical_cut(g, cut_start, height + cut_def['cut_width'] + width + depth*.5, cut_def['x_movement'], conical_mill_diameter, 'x')

    # y cuts
    define_conical_cut(g, height + depth, cut_start, cut_def['y_movement'], conical_mill_diameter, 'y')
    define_conical_cut(g, height + cut_def['cut_width'] + length + depth*.5, cut_start, cut_def['y_movement'], conical_mill_diameter, 'y')

def main():
    # unit = prompt('Unit Type - inch or mm', defaultValue="inch", normfunc=_valid_units, retry=True)
    # unit_plural = unit+"s"
    # length = prompt_num('Base length in %s' % unit_plural, retry=True)
    # width = prompt_num('Base width in %s' % unit_plural, retry=True)
    # height = prompt_num('Side height in %s' % unit_plural, retry=True)
    # depth = prompt_num('Stock depth in %s' % unit_plural, retry=True)

    length = 10
    width = 10
    height = 15
    depth = 2
    tool_size = .5
    cylindrical_mill_diameter = .5
    conical_mill_diameter = .5
    step_down = .25

    cut_def['cut_width'] = depth*OUTER_CUT_WIDTH_FACTOR
    cut_def['out_cut'] = (depth*OUTER_CUT_WIDTH_FACTOR)-cylindrical_mill_diameter
    cut_def['inner_cut'] = (depth*INNNER_CUT_WIDTH_FACTOR)-cylindrical_mill_diameter
    cut_def['out_depth'] = OUTER_CUT_DEPTH_FACTOR*depth
    cut_def['inner_depth'] = INNNER_CUT_DEPTH_FACTOR*depth
    cut_def['full_depth'] = depth
    cut_def['over_lap'] = cylindrical_mill_diameter*OVER_LAP_FACTOR
    cut_def['tool_half_diameter'] = cylindrical_mill_diameter / 2
    cut_def['y_movement'] = 2*max(conical_mill_diameter+.1, cylindrical_mill_diameter+.1) + 2*height + 2*cut_def['cut_width'] + width
    cut_def['x_movement'] = 2*max(conical_mill_diameter+.1, cylindrical_mill_diameter+.1) + 2*height + 2*cut_def['cut_width'] + length

    with G(direct_write=False, header=None, setup=False, print_lines=True) as g:
        #header
        g.write("G20 G90 G40")

        g.absolute()
        g.setup()

        g.feed(30)
        define_flat_cuts(g, length, width, height, depth, cylindrical_mill_diameter)
        define_conical_cuts(g, length, width, height, depth, conical_mill_diameter)

        #end
        g.move(z=.5)
        g.move(x=0, y=0)

        #view(g)

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


if __name__ == '__main__':
    main()
