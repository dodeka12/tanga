//////////////////////////////////////////////////////////////////////////////////
// <<licence: start>>
//
// This file is part of the TANGA library, 
// a template library that implements geometric algebra.
//
// Copyright 2022 Christian Perwass
//
//    Licensed under the Apache License, Version 2.0 (the "License");
//    you may not use this file except in compliance with the License.
//    You may obtain a copy of the License at
//
//        http://www.apache.org/licenses/LICENSE-2.0
//
//    Unless required by applicable law or agreed to in writing, software
//    distributed under the License is distributed on an "AS IS" BASIS,
//    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//    See the License for the specific language governing permissions and
//    limitations under the License.
//
// <<licence: end>>
//////////////////////////////////////////////////////////////////////////////////


#pragma once

#include <cassert>
#include <cstring>
#include <exception>
#include <stdexcept>

#ifdef _WIN32
#	define TAN_ASSERT(theCond) assert(theCond)
#else
#	ifdef _DEBUG
#		define TAN_ASSERT(theCond) if (!(theCond)) TAN_THROW_RT("Assertion failed")
#	else
#		define TAN_ASSERT(theCond) 
#	endif
#endif

#define __HOSTDEV__ 
#define __HDINL__ inline
#define __INLINE__ inline

#define TAN_EXCEPTION_TEXT(theText) std::string(__FUNCTION__) + ", line " + std::to_string(__LINE__) + ": " + std::string(theText)
#define TAN_THROW_RT(theText) throw std::runtime_error(TAN_EXCEPTION_TEXT(theText))
#define TAN_RETHROW(theText, theEx) throw std::runtime_error(std::string(theEx.what()) + "\n" + TAN_EXCEPTION_TEXT(theText))

#ifndef __noop
#	define __noop ((void)0)
#endif

#ifdef _DEBUG
#	define TAN_TEST_PROD_OVERFLOW(theValA, theValB) \
					if (Tan::Intrinsics::ProductWillOverflow(theValA, theValB)) \
					{ TAN_THROW_RT("Overflow in product"); }

#	define TAN_TEST_SUM_OVERFLOW(theValA, theValB) \
					if (Tan::Intrinsics::SumWillOverflow(theValA, theValB)) \
					{ TAN_THROW_RT("Sum overflow."); }

#else
#	define TAN_TEST_PROD_OVERFLOW(theValA, theValB) __noop
#	define TAN_TEST_SUM_OVERFLOW(theValA, theValB) __noop
#endif


// ///////////////////////////////////////////////////////////////////
// Static Assert
#define TAN_STATIC_ASSERT(theCondition) \
	typedef SStaticAssertTest< \
			sizeof(STATIC_ASSERTION_FAILURE< (bool)(theCondition) >) \
					> TStaticAssertTypedef

template<bool t_bValue>
struct STATIC_ASSERTION_FAILURE;

template<> struct STATIC_ASSERTION_FAILURE<true>
{
	char cDummy;
};

template<int t_iValue> struct SStaticAssertTest { };
