
// mirror([0, 0, 1]) import("grass.stl");

//////////////
// STRAIGHT //
//////////////

// // tracks
// translate([ .09, 0, .025]) cube([.03, 1, .03], true);
// translate([-.09, 0, .025]) cube([.03, 1, .03], true);

// // ends
// translate([0, .475, .015]) cube([.3, .05, .03], true);
// translate([0,-.475, .015]) cube([.3, .05, .03], true);

// // beats
// translate([0, .25, .015]) cube([.3, .1, .03], true);
// translate([0,-.25, .015]) cube([.3, .1, .03], true);
// translate([0, 0, .015]) cube([.3, .1, .03], true);

////////////
// CURVED //
////////////

$fn = 64;

rotate([0, 0, 30]) {

    // tracks
    translate([0, 1, .025])
    rotate([0, 0, -120]) rotate_extrude(angle=60)
    translate([.956, 0, 0]) square([.03, .03], true);
    translate([0, 1, .025])
    rotate([0, 0, -120]) rotate_extrude(angle=60)
    translate([.776, 0, 0]) square([.03, .03], true);

    // ends
    rotate([0, 0, 60])
    translate([0, .475, .015]) cube([.3, .05, .03], true);
    rotate([0, 0, 120])
    translate([0,-.475, .015]) cube([.3, .05, .03], true);

    // beats
    translate([0, 1, 0]) rotate([0, 0, 0])
    translate([0, -.866, .015]) cylinder(.1, .01, .01);//cube([.1, .3, .03], true);
    translate([0, 1, 0]) rotate([0, 0, 15])
    translate([0, -.866, .015]) cylinder(.1, .01, .01);//cube([.1, .3, .03], true);
    translate([0, 1, 0]) rotate([0, 0,-15])
    translate([0, -.866, .015]) cylinder(.1, .01, .01);//cube([.1, .3, .03], true);

}

#translate([-.5, 0, 0]) cylinder(.1, .01, .01);
#translate([-.276, .029, 0]) cylinder(.1, .01, .01);
#translate([-.067, .116, 0]) cylinder(.1, .01, .01);
#translate([.112, .253, 0]) cylinder(.1, .01, .01);
#translate([.25, .433, 0]) cylinder(.1, .01, .01);