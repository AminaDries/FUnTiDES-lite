// Auto-generated file - DO NOT EDIT
// Generated for: SEMQ3 struct makutu solver modelonnodes

#include <model_struct.h>

#include "sem_solver_acoustic_impl.h"

constexpr int ORDER = 3;

template class SEMsolverAcoustic<ORDER, 
                         IntegralTypeSelector<ORDER, IntegralType::MAKUTU>::type,
                         model::ModelStruct<float, int, ORDER>, true>;
