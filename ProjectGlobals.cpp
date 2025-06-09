// Contents of PythonWrapper/ADCBoardControlPython/ProjectGlobals.cpp

#include "headers/CommonIncludes.h" // For InstallSegFaultHandler (inline) and isSegFaultHandlerInstalled declaration
#include "headers/Error.h" // For MainErrorCollector, Verbosity, ErrorStream declarations
#include <iostream> // For std::cerr

// Actual DEFINITIONS of global variables from Error.h
int Verbosity = 0; // Default to 0 (false). Your original `Error.h` had `false`.
std::ostream *ErrorStream = &std::cerr;
FGErrorCollector
    MainErrorCollector(nullptr); // Default constructor as in your Error.h

// Actual DEFINITION of global variable from CommonIncludes.h (segfault part)
// InstallSegFaultHandler() is now inline in CommonIncludes.h, so it's defined
// when CommonIncludes.h is included.
#ifdef SEGHANDLER // This guard should match the one in CommonIncludes.h
bool isSegFaultHandlerInstalled = InstallSegFaultHandler();
#endif