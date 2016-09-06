#define CATCH_CONFIG_MAIN
#include <casacore/measures/Measures/Stokes.h>
#include <complex.h>
#undef I
#undef complex

#include "catch.hpp"
#include "../Stokes.h"

TEST_CASE( "Test circular correlation to stokes", "[circ2stokes]" ) {
    int in[4] = {casacore::Stokes::RR, casacore::Stokes::RL, casacore::Stokes::LR, casacore::Stokes::LL};
    int out[4] = {casacore::Stokes::I, casacore::Stokes::Q, casacore::Stokes::U, casacore::Stokes::V};
    {
      //I = 1
      float _Complex data[4] = {1+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I,1+0*_Complex_I};
      float _Complex data_out[4] = {0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I};
      init_stokes_converter(4,4,in,out);
      convert_corrs_32(data,data_out);
      free_stokes_library();
      REQUIRE(data_out[0] == 1+0*_Complex_I);
      REQUIRE(data_out[1] == 0+0*_Complex_I);
      REQUIRE(data_out[2] == 0+0*_Complex_I);
      REQUIRE(data_out[3] == 0+0*_Complex_I);
    }
    {
      //I=1,U=1,Q=0
      float _Complex data[4] = {1+0*_Complex_I,0+1*_Complex_I,0-1*_Complex_I,1+0*_Complex_I};
      float _Complex data_out[4] = {0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I};
      init_stokes_converter(4,4,in,out);
      convert_corrs_32(data,data_out);
      free_stokes_library();
      REQUIRE(data_out[0] == 1+0*_Complex_I);
      REQUIRE(data_out[1] == 0+0*_Complex_I);
      REQUIRE(data_out[2] == 1+0*_Complex_I);
      REQUIRE(data_out[3] == 0+0*_Complex_I);
    }
    {
      //I=1,U=0.25,Q=0.75
      float _Complex data[4] = {1.0+0*_Complex_I,0.75+0.25*_Complex_I,0.75-0.25*_Complex_I,1.0+0*_Complex_I};
      float _Complex data_out[4] = {0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I};
      init_stokes_converter(4,4,in,out);
      convert_corrs_32(data,data_out);
      free_stokes_library();
      REQUIRE(data_out[0] == 1+0*_Complex_I);
      REQUIRE(data_out[1] == 0.75+0*_Complex_I);
      REQUIRE(data_out[2] == 0.25+0*_Complex_I);
      REQUIRE(data_out[3] == 0+0*_Complex_I);
    }
    {
      //I=4,U=0.25,Q=0.75,V=3
      float _Complex data[4] = {7+0*_Complex_I,0.75+0.25*_Complex_I,0.75-0.25*_Complex_I,1+0*_Complex_I};
      float _Complex data_out[4] = {0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I};
      init_stokes_converter(4,4,in,out);
      convert_corrs_32(data,data_out);
      free_stokes_library();
      REQUIRE(data_out[0] == 4+0*_Complex_I);
      REQUIRE(data_out[1] == 0.75+0*_Complex_I);
      REQUIRE(data_out[2] == 0.25+0*_Complex_I);
      REQUIRE(data_out[3] == 3+0*_Complex_I);
    }
}

TEST_CASE( "Test stokes to circular correlation", "[stokes2circ]" ) {
    int out[4] = {casacore::Stokes::RR, casacore::Stokes::RL, casacore::Stokes::LR, casacore::Stokes::LL};
    int in[4] = {casacore::Stokes::I, casacore::Stokes::Q, casacore::Stokes::U, casacore::Stokes::V};
    {
      //I = 1
      float _Complex data[4] = {1+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I};
      float _Complex data_out[4] = {0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I};
      init_stokes_converter(4,4,in,out);
      convert_corrs_32(data,data_out);
      free_stokes_library();
      REQUIRE(data_out[0] == 1+0*_Complex_I);
      REQUIRE(data_out[1] == 0+0*_Complex_I);
      REQUIRE(data_out[2] == 0+0*_Complex_I);
      REQUIRE(data_out[3] == 1+0*_Complex_I);
    }
    {
      //I=1,U=1,Q=0
      float _Complex data[4] = {1+0*_Complex_I,0+0*_Complex_I,1+0*_Complex_I,0+0*_Complex_I};
      float _Complex data_out[4] = {0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I};
      init_stokes_converter(4,4,in,out);
      convert_corrs_32(data,data_out);
      free_stokes_library();
      REQUIRE(data_out[0] == 1+0*_Complex_I);
      REQUIRE(data_out[1] == 0+1*_Complex_I);
      REQUIRE(data_out[2] == 0-1*_Complex_I);
      REQUIRE(data_out[3] == 1+0*_Complex_I);
    }
    {
      //I=1,U=0.25,Q=0.75
      float _Complex data[4] = {1.0+0*_Complex_I,0.75+0*_Complex_I,0.25-0*_Complex_I,0+0*_Complex_I};
      float _Complex data_out[4] = {0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I};
      init_stokes_converter(4,4,in,out);
      convert_corrs_32(data,data_out);
      free_stokes_library();
      REQUIRE(data_out[0] == 1+0*_Complex_I);
      REQUIRE(data_out[1] == 0.75+0.25*_Complex_I);
      REQUIRE(data_out[2] == 0.75-0.25*_Complex_I);
      REQUIRE(data_out[3] == 1+0*_Complex_I);
    }
    {
      //I=4,U=0.25,Q=0.75,V=3
      float _Complex data[4] = {4+0*_Complex_I,0.75+0*_Complex_I,0.25-0*_Complex_I,3+0*_Complex_I};
      float _Complex data_out[4] = {0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I};
      init_stokes_converter(4,4,in,out);
      convert_corrs_32(data,data_out);
      free_stokes_library();
      REQUIRE(data_out[0] == 7+0*_Complex_I);
      REQUIRE(data_out[1] == 0.75+0.25*_Complex_I);
      REQUIRE(data_out[2] == 0.75-0.25*_Complex_I);
      REQUIRE(data_out[3] == 1+0*_Complex_I);
    }
}

TEST_CASE( "Test circular correlation to stokes double", "[circ2stokesdbl]" ) {
    int in[4] = {casacore::Stokes::RR, casacore::Stokes::RL, casacore::Stokes::LR, casacore::Stokes::LL};
    int out[4] = {casacore::Stokes::I, casacore::Stokes::Q, casacore::Stokes::U, casacore::Stokes::V};
    {
      //I = 1
      double _Complex data[4] = {1+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I,1+0*_Complex_I};
      double _Complex data_out[4] = {0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I};
      init_stokes_converter(4,4,in,out);
      convert_corrs_64(data,data_out);
      free_stokes_library();
      REQUIRE(data_out[0] == 1+0*_Complex_I);
      REQUIRE(data_out[1] == 0+0*_Complex_I);
      REQUIRE(data_out[2] == 0+0*_Complex_I);
      REQUIRE(data_out[3] == 0+0*_Complex_I);
    }
    {
      //I=1,U=1,Q=0
      double _Complex data[4] = {1+0*_Complex_I,0+1*_Complex_I,0-1*_Complex_I,1+0*_Complex_I};
      double _Complex data_out[4] = {0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I};
      init_stokes_converter(4,4,in,out);
      convert_corrs_64(data,data_out);
      free_stokes_library();
      REQUIRE(data_out[0] == 1+0*_Complex_I);
      REQUIRE(data_out[1] == 0+0*_Complex_I);
      REQUIRE(data_out[2] == 1+0*_Complex_I);
      REQUIRE(data_out[3] == 0+0*_Complex_I);
    }
    {
      //I=1,U=0.25,Q=0.75
      double _Complex data[4] = {1.0+0*_Complex_I,0.75+0.25*_Complex_I,0.75-0.25*_Complex_I,1.0+0*_Complex_I};
      double _Complex data_out[4] = {0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I};
      init_stokes_converter(4,4,in,out);
      convert_corrs_64(data,data_out);
      free_stokes_library();
      REQUIRE(data_out[0] == 1+0*_Complex_I);
      REQUIRE(data_out[1] == 0.75+0*_Complex_I);
      REQUIRE(data_out[2] == 0.25+0*_Complex_I);
      REQUIRE(data_out[3] == 0+0*_Complex_I);
    }
    {
      //I=4,U=0.25,Q=0.75,V=3
      double _Complex data[4] = {7+0*_Complex_I,0.75+0.25*_Complex_I,0.75-0.25*_Complex_I,1+0*_Complex_I};
      double _Complex data_out[4] = {0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I};
      init_stokes_converter(4,4,in,out);
      convert_corrs_64(data,data_out);
      free_stokes_library();
      REQUIRE(data_out[0] == 4+0*_Complex_I);
      REQUIRE(data_out[1] == 0.75+0*_Complex_I);
      REQUIRE(data_out[2] == 0.25+0*_Complex_I);
      REQUIRE(data_out[3] == 3+0*_Complex_I);
    }
}

TEST_CASE( "Test stokes to circular correlation double", "[stokes2circdbl]" ) {
    int out[4] = {casacore::Stokes::RR, casacore::Stokes::RL, casacore::Stokes::LR, casacore::Stokes::LL};
    int in[4] = {casacore::Stokes::I, casacore::Stokes::Q, casacore::Stokes::U, casacore::Stokes::V};
    {
      //I = 1
      double _Complex data[4] = {1+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I};
      double _Complex data_out[4] = {0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I};
      init_stokes_converter(4,4,in,out);
      convert_corrs_64(data,data_out);
      free_stokes_library();
      REQUIRE(data_out[0] == 1+0*_Complex_I);
      REQUIRE(data_out[1] == 0+0*_Complex_I);
      REQUIRE(data_out[2] == 0+0*_Complex_I);
      REQUIRE(data_out[3] == 1+0*_Complex_I);
    }
    {
      //I=1,U=1,Q=0
      double _Complex data[4] = {1+0*_Complex_I,0+0*_Complex_I,1+0*_Complex_I,0+0*_Complex_I};
      double _Complex data_out[4] = {0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I};
      init_stokes_converter(4,4,in,out);
      convert_corrs_64(data,data_out);
      free_stokes_library();
      REQUIRE(data_out[0] == 1+0*_Complex_I);
      REQUIRE(data_out[1] == 0+1*_Complex_I);
      REQUIRE(data_out[2] == 0-1*_Complex_I);
      REQUIRE(data_out[3] == 1+0*_Complex_I);
    }
    {
      //I=1,U=0.25,Q=0.75
      double _Complex data[4] = {1.0+0*_Complex_I,0.75+0*_Complex_I,0.25-0*_Complex_I,0+0*_Complex_I};
      double _Complex data_out[4] = {0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I};
      init_stokes_converter(4,4,in,out);
      convert_corrs_64(data,data_out);
      free_stokes_library();
      REQUIRE(data_out[0] == 1+0*_Complex_I);
      REQUIRE(data_out[1] == 0.75+0.25*_Complex_I);
      REQUIRE(data_out[2] == 0.75-0.25*_Complex_I);
      REQUIRE(data_out[3] == 1+0*_Complex_I);
    }
    {
      //I=4,U=0.25,Q=0.75,V=3
      double _Complex data[4] = {4+0*_Complex_I,0.75+0*_Complex_I,0.25-0*_Complex_I,3+0*_Complex_I};
      double _Complex data_out[4] = {0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I};
      init_stokes_converter(4,4,in,out);
      convert_corrs_64(data,data_out);
      free_stokes_library();
      REQUIRE(data_out[0] == 7+0*_Complex_I);
      REQUIRE(data_out[1] == 0.75+0.25*_Complex_I);
      REQUIRE(data_out[2] == 0.75-0.25*_Complex_I);
      REQUIRE(data_out[3] == 1+0*_Complex_I);
    }
}

TEST_CASE( "Test give PSF vis float", "[psf_vis_float]" )
{
  int out[4] = {casacore::Stokes::RR, casacore::Stokes::RL, casacore::Stokes::LR, casacore::Stokes::LL};
  float _Complex data_out[4] = {0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I};
  give_psf_vis_32(4,out,data_out);
  REQUIRE(data_out[0] == 2+0*_Complex_I); //I+V
  REQUIRE(data_out[1] == 1+1*_Complex_I); //Q+iU
  REQUIRE(data_out[2] == 1-1*_Complex_I); //Q-iU
  REQUIRE(data_out[3] == 0+0*_Complex_I); //I-V
}

TEST_CASE( "Test give PSF vis double", "[psf_vis_double]" )
{
  int out[4] = {casacore::Stokes::RR, casacore::Stokes::RL, casacore::Stokes::LR, casacore::Stokes::LL};
  double _Complex data_out[4] = {0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I,0+0*_Complex_I};
  give_psf_vis_64(4,out,data_out);
  REQUIRE(data_out[0] == 2+0*_Complex_I); //I+V
  REQUIRE(data_out[1] == 1+1*_Complex_I); //Q+iU
  REQUIRE(data_out[2] == 1-1*_Complex_I); //Q-iU
  REQUIRE(data_out[3] == 0+0*_Complex_I); //I-V
}

TEST_CASE( "Test I to XX,YY", "[I_XXYY]" )
{
  double _Complex data[1] = {3+0*_Complex_I};
  double _Complex data_out[2] = {0+0*_Complex_I, 0+0*_Complex_I};
  int in[1] = {casacore::Stokes::I};
  int out[2] = {casacore::Stokes::XX, casacore::Stokes::YY};
  
  init_stokes_converter(1,2,in,out);
  
  convert_corrs_64(data,data_out);
  free_stokes_library();
  REQUIRE(data_out[0] == 3+0*_Complex_I);
  REQUIRE(data_out[1] == 3+0*_Complex_I);
}

TEST_CASE( "Test I to RR,LL", "[I_RRLL]" )
{
  double _Complex data[1] = {3+0*_Complex_I};
  double _Complex data_out[2] = {0+0*_Complex_I, 0+0*_Complex_I};
  int in[1] = {casacore::Stokes::I};
  int out[2] = {casacore::Stokes::RR, casacore::Stokes::LL};
  init_stokes_converter(1,2,in,out);
  convert_corrs_64(data,data_out);
  free_stokes_library();
  REQUIRE(data_out[0] == 3+0*_Complex_I);
  REQUIRE(data_out[1] == 3+0*_Complex_I);
}

TEST_CASE( "Test I to RR,RL,LR,LL", "[I_RRRLLRLL]" )
{
  double _Complex data[1] = {3+0*_Complex_I};
  double _Complex data_out[4] = {0+0*_Complex_I, 0+0*_Complex_I, 0+0*_Complex_I, 0+0*_Complex_I};
  int in[1] = {casacore::Stokes::I};
  int out[4] = {casacore::Stokes::RR, casacore::Stokes::RL, casacore::Stokes::LR, casacore::Stokes::LL};
  init_stokes_converter(1,4,in,out);
  convert_corrs_64(data,data_out);
  free_stokes_library();
  REQUIRE(data_out[0] == 3+0*_Complex_I);
  REQUIRE(data_out[1] == 0+0*_Complex_I);
  REQUIRE(data_out[2] == 0+0*_Complex_I);
  REQUIRE(data_out[3] == 3+0*_Complex_I);
}

TEST_CASE( "Test I to XX,XY,YX,YY", "[I_XXXYYXYY]" )
{
  double _Complex data[1] = {3+0*_Complex_I};
  double _Complex data_out[4] = {0+0*_Complex_I, 0+0*_Complex_I, 0+0*_Complex_I, 0+0*_Complex_I};
  int in[1] = {casacore::Stokes::I};
  int out[4] = {casacore::Stokes::RR, casacore::Stokes::RL, casacore::Stokes::LR, casacore::Stokes::LL};
  init_stokes_converter(1,4,in,out);
  convert_corrs_64(data,data_out);
  free_stokes_library();
  REQUIRE(data_out[0] == 3+0*_Complex_I);
  REQUIRE(data_out[1] == 0+0*_Complex_I);
  REQUIRE(data_out[2] == 0+0*_Complex_I);
  REQUIRE(data_out[3] == 3+0*_Complex_I);
}