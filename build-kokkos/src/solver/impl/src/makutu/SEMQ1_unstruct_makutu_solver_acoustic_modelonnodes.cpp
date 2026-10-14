// Auto-generated file - DO NOT EDIT
// Generated for: SEMQ1 unstruct makutu solver modelonnodes

#include <model_unstruct.h>

#include "sem_solver_acoustic_impl.h"

constexpr int ORDER = 1;

template class SEMsolverAcoustic<ORDER, 
                         IntegralTypeSelector<ORDER, IntegralType::MAKUTU>::type,
                         model::ModelUnstruct<float, int>, true>;
