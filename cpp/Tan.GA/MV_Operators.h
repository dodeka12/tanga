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

#include "Blade_Operators.h"
#include "BladeMask.h"

namespace Tan
{
	namespace GA
	{
		template <class TValue, typename TBlade, unsigned t_uSubspaceDimension>
		class _CSubspaceMultivector;
		template <class _TValue, typename _TBlade>
		class _CMultivector;
		template <class _TValue, typename _TBlade>
		class CMultivector;
		template <typename _TValue, typename _TBlade>
		class CDynamicMultivector;

		template <typename TMultivectorC, typename TMultivectorA, typename TMultivectorB,
				  typename FuncOp, typename FuncAdd, typename FuncInvolution, typename FuncInvolSign>
		void Product(TMultivectorC &wC,
					 const TMultivectorA &wA,
					 const bool bInvoluteA,
					 const TMultivectorB &wB,
					 const bool bInvoluteB,
					 FuncOp xFuncOp,
					 FuncAdd xFuncAdd,
					 FuncInvolution xFuncInvolution,
					 FuncInvolSign xFuncInvolSign)
		{
			TAN_ASSERT(wC.IsValid());
			TAN_ASSERT(wA.IsValid());
			TAN_ASSERT(wB.IsValid());

			if ((wA.GetBladeCount() == 0) || (wB.GetBladeCount() == 0))
			{
				wC.Zero();
			}
			else
			{
				wC.Zero();

				if (bInvoluteA)
				{
					if (bInvoluteB)
					{
						// Using the identity:
						// ~A * ~B = ~(B*A)
						// This holds for reversion and conjugation

						// Calculate C = B * A
						wB.ForEachBlade([&](const typename TMultivectorB::TValue &fValB, const typename TMultivectorB::TBlade &blB)
										{ ProductInnerLoop_A(wC, fValB, blB, wA, xFuncOp, xFuncAdd); });

						// Calculate ~C
						xFuncInvolution(wC);
					}
					else
					{
						wA.ForEachBlade([&](const typename TMultivectorA::TValue &fValA, const typename TMultivectorA::TBlade &blA)
										{
									auto fValue = fValA;

									if (xFuncInvolSign(blA))
									{
										fValue = -fValA;
									}

									ProductInnerLoop_A(wC, fValue, blA, wB, xFuncOp, xFuncAdd); });
					}
				}
				else if (bInvoluteB)
				{
					wB.ForEachBlade([&](const typename TMultivectorB::TValue &fValB, const typename TMultivectorB::TBlade &blB)
									{
								auto fValue = fValB;

								if (xFuncInvolSign(blB))
								{
									fValue = -fValB;
								}

								ProductInnerLoop_B(wC, wA, fValue, blB, xFuncOp, xFuncAdd); });
				}
				else
				{
					wA.ForEachBlade([&](const typename TMultivectorA::TValue &fValA, const typename TMultivectorA::TBlade &blA)
									{ ProductInnerLoop_A(wC, fValA, blA, wB, xFuncOp, xFuncAdd); });
				}
			}
		}

		template <typename TMultivectorC, typename TValueA, typename TBladeA, typename TMultivectorB, typename FuncOp, typename FuncAdd>
		void ProductInnerLoop_A(TMultivectorC &wC, const TValueA &fValA, const TBladeA &blA, const TMultivectorB &wB, FuncOp xFuncOp, FuncAdd xFuncAdd)
		{
			wB.ForEachBlade([&](const typename TMultivectorB::TValue &fValB, const typename TMultivectorB::TBlade &blB)
							{ ProductOperator(wC, fValA, blA, fValB, blB, xFuncOp, xFuncAdd); });
		}

		template <typename TMultivectorC, typename TMultivectorA, typename TValueB, typename TBladeB, typename FuncOp, typename FuncAdd>
		void ProductInnerLoop_B(TMultivectorC &wC, const TMultivectorA &wA, const TValueB &fValB, const TBladeB &blB, FuncOp xFuncOp, FuncAdd xFuncAdd)
		{
			wA.ForEachBlade([&](const typename TMultivectorA::TValue &fValA, const typename TMultivectorA::TBlade &blA)
							{ ProductOperator(wC, fValA, blA, fValB, blB, xFuncOp, xFuncAdd); });
		}

		template <typename TMultivectorC, typename TValueA, typename TBladeA, typename TValueB, typename TBladeB, typename FuncOp, typename FuncAdd>
		void ProductOperator(TMultivectorC &wC, const TValueA &fValA, const TBladeA &blA, const TValueB &fValB, const TBladeB &blB, FuncOp xFuncOp, FuncAdd xFuncAdd)
		{
			typename TMultivectorC::TValue fValC;
			typename TMultivectorC::TBlade blC;

			if (xFuncOp(fValC, blC, fValA, blA, fValB, blB))
			{
				// wC.AddValueBlade(fValC, blC);
				xFuncAdd(wC, fValC, blC);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	G ps.
		/// </summary>
		///
		/// <typeparam name="typename TMultivectorC">	Type of the typename t multivector c. </typeparam>
		/// <typeparam name="typename TMultivectorA">	Type of the typename t multivector a. </typeparam>
		/// <typeparam name="typename TMultivectorB">	Type of the typename t multivector b. </typeparam>
		/// <param name="wC">	[in,out] The w c. </param>
		/// <param name="wA">	The w a. </param>
		/// <param name="wB">	The w b. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TMultivectorC, typename TMultivectorA, typename TMultivectorB>
		void GP(TMultivectorC &wC, const TMultivectorA &wA, const TMultivectorB &wB)
		{
			Product(wC, wA, false, wB, false, [](typename TMultivectorC::TValue &fValC, typename TMultivectorC::TBlade &blC, const typename TMultivectorA::TValue &fValA, const typename TMultivectorA::TBlade &blA, const typename TMultivectorB::TValue &fValB, const typename TMultivectorB::TBlade &blB) -> bool
					{ return GA::GP(fValC, blC, fValA, blA, fValB, blB); }, [](TMultivectorC &wC, const typename TMultivectorC::TValue &fValC, const typename TMultivectorC::TBlade &blC)
					{ wC.AddValueBlade(fValC, blC); }, [](TMultivectorC &wX)
					{ return; }, [](const typename TMultivectorC::TBlade &blX) -> unsigned
					{ return 0; });
		}

		template <typename TMultivectorC, typename TMultivectorA, typename TMultivectorB, typename TCongruence>
		void GP_Congruence(TMultivectorC &wC, const TMultivectorA &wA, const TMultivectorB &wB, const TCongruence &xCongruence)
		{
			Product(wC, wA, false, wB, false, [&xCongruence](typename TMultivectorC::TValue &fValC, typename TMultivectorC::TBlade &blC, const typename TMultivectorA::TValue &fValA, const typename TMultivectorA::TBlade &blA, const typename TMultivectorB::TValue &fValB, const typename TMultivectorB::TBlade &blB) -> bool
					{ return GA::GP(fValC, blC, fValA, blA, fValB, blB, xCongruence); }, [&xCongruence](TMultivectorC &wC, const typename TMultivectorC::TValue &fValC, const typename TMultivectorC::TBlade &blC)
					{ wC.AddValueBlade(fValC, blC, xCongruence); }, [](TMultivectorC &wX)
					{ return; }, [](const typename TMultivectorC::TBlade &blX) -> unsigned
					{ return 0; });
		}

		template <typename TMultivectorC, typename TMultivectorA, typename TMultivectorB>
		void GP_Reverse(TMultivectorC &wC, const TMultivectorA &wA, const bool bReverseA, const TMultivectorB &wB, const bool bReverseB)
		{
			Product(wC, wA, bReverseA, wB, bReverseB, [](typename TMultivectorC::TValue &fValC, typename TMultivectorC::TBlade &blC, const typename TMultivectorA::TValue &fValA, const typename TMultivectorA::TBlade &blA, const typename TMultivectorB::TValue &fValB, const typename TMultivectorB::TBlade &blB) -> bool
					{ return GA::GP(fValC, blC, fValA, blA, fValB, blB); }, [](TMultivectorC &wC, const typename TMultivectorC::TValue &fValC, const typename TMultivectorC::TBlade &blC)
					{ wC.AddValueBlade(fValC, blC); }, [](TMultivectorC &wX)
					{ Reverse(wX); }, [](const typename TMultivectorC::TBlade &blX) -> unsigned
					{ return blX.GetReverseSign(); });
		}

		template <typename TMultivectorC, typename TMultivectorA, typename TMultivectorB>
		void GP_Conjugate(TMultivectorC &wC, const TMultivectorA &wA, const bool bConjugateA, const TMultivectorB &wB, const bool bConjugateB)
		{
			Product(wC, wA, bConjugateA, wB, bConjugateB, [](typename TMultivectorC::TValue &fValC, typename TMultivectorC::TBlade &blC, const typename TMultivectorA::TValue &fValA, const typename TMultivectorA::TBlade &blA, const typename TMultivectorB::TValue &fValB, const typename TMultivectorB::TBlade &blB) -> bool
					{ return GA::GP(fValC, blC, fValA, blA, fValB, blB); }, [](TMultivectorC &wC, const typename TMultivectorC::TValue &fValC, const typename TMultivectorC::TBlade &blC)
					{ wC.AddValueBlade(fValC, blC); }, [](TMultivectorC &wX)
					{ Conjugate(wX); }, [](const typename TMultivectorC::TBlade &blX) -> unsigned
					{ return blX.GetConjugateSign(); });
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	I ps.
		/// </summary>
		///
		/// <typeparam name="typename TMultivectorC">	Type of the typename t multivector c. </typeparam>
		/// <typeparam name="typename TMultivectorA">	Type of the typename t multivector a. </typeparam>
		/// <typeparam name="typename TMultivectorB">	Type of the typename t multivector b. </typeparam>
		/// <param name="wC">	[in,out] The w c. </param>
		/// <param name="wA">	The w a. </param>
		/// <param name="wB">	The w b. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TMultivectorC, typename TMultivectorA, typename TMultivectorB>
		void IP(TMultivectorC &wC, const TMultivectorA &wA, const TMultivectorB &wB)
		{
			Product(wC, wA, false, wB, false, [](typename TMultivectorC::TValue &fValC, typename TMultivectorC::TBlade &blC, const typename TMultivectorA::TValue &fValA, const typename TMultivectorA::TBlade &blA, const typename TMultivectorB::TValue &fValB, const typename TMultivectorB::TBlade &blB) -> bool
					{ return GA::IP(fValC, blC, fValA, blA, fValB, blB); }, [](TMultivectorC &wC, const typename TMultivectorC::TValue &fValC, const typename TMultivectorC::TBlade &blC)
					{ wC.AddValueBlade(fValC, blC); }, [](TMultivectorC &wX)
					{ return; }, [](const typename TMultivectorC::TBlade &blX) -> unsigned
					{ return 0; });
		}

		template <typename TMultivectorC, typename TMultivectorA, typename TMultivectorB>
		void IP_Reverse(TMultivectorC &wC, const TMultivectorA &wA, const bool bReverseA, const TMultivectorB &wB, const bool bReverseB)
		{
			Product(wC, wA, bReverseA, wB, bReverseB, [](typename TMultivectorC::TValue &fValC, typename TMultivectorC::TBlade &blC, const typename TMultivectorA::TValue &fValA, const typename TMultivectorA::TBlade &blA, const typename TMultivectorB::TValue &fValB, const typename TMultivectorB::TBlade &blB) -> bool
					{ return GA::IP(fValC, blC, fValA, blA, fValB, blB); }, [](TMultivectorC &wC, const typename TMultivectorC::TValue &fValC, const typename TMultivectorC::TBlade &blC)
					{ wC.AddValueBlade(fValC, blC); }, [](TMultivectorC &wX)
					{ Reverse(wX); }, [](const typename TMultivectorC::TBlade &blX) -> unsigned
					{ return blX.GetReverseSign(); });
		}

		template <typename TMultivectorC, typename TMultivectorA, typename TMultivectorB>
		void IP_Conjugate(TMultivectorC &wC, const TMultivectorA &wA, const bool bConjugateA, const TMultivectorB &wB, const bool bConjugateB)
		{
			Product(wC, wA, bConjugateA, wB, bConjugateB, [](typename TMultivectorC::TValue &fValC, typename TMultivectorC::TBlade &blC, const typename TMultivectorA::TValue &fValA, const typename TMultivectorA::TBlade &blA, const typename TMultivectorB::TValue &fValB, const typename TMultivectorB::TBlade &blB) -> bool
					{ return GA::IP(fValC, blC, fValA, blA, fValB, blB); }, [](TMultivectorC &wC, const typename TMultivectorC::TValue &fValC, const typename TMultivectorC::TBlade &blC)
					{ wC.AddValueBlade(fValC, blC); }, [](TMultivectorC &wX)
					{ Conjugate(wX); }, [](const typename TMultivectorC::TBlade &blX) -> unsigned
					{ return blX.GetConjugateSign(); });
		}

		template <typename TMultivectorC, typename TMultivectorA, typename TMultivectorB>
		void OP(TMultivectorC &wC, const TMultivectorA &wA, const TMultivectorB &wB)
		{
			Product(wC, wA, false, wB, false, [](typename TMultivectorC::TValue &fValC, typename TMultivectorC::TBlade &blC, const typename TMultivectorA::TValue &fValA, const typename TMultivectorA::TBlade &blA, const typename TMultivectorB::TValue &fValB, const typename TMultivectorB::TBlade &blB) -> bool
					{ return GA::OP(fValC, blC, fValA, blA, fValB, blB); }, [](TMultivectorC &wC, const typename TMultivectorC::TValue &fValC, const typename TMultivectorC::TBlade &blC)
					{ wC.AddValueBlade(fValC, blC); }, [](TMultivectorC &wX)
					{ return; }, [](const typename TMultivectorC::TBlade &blX) -> unsigned
					{ return 0; });
		}

		template <typename TMultivectorC, typename TMultivectorA, typename TMultivectorB>
		void OP_Reverse(TMultivectorC &wC, const TMultivectorA &wA, const bool bReverseA, const TMultivectorB &wB, const bool bReverseB)
		{
			Product(wC, wA, bReverseA, wB, bReverseB, [](typename TMultivectorC::TValue &fValC, typename TMultivectorC::TBlade &blC, const typename TMultivectorA::TValue &fValA, const typename TMultivectorA::TBlade &blA, const typename TMultivectorB::TValue &fValB, const typename TMultivectorB::TBlade &blB) -> bool
					{ return GA::OP(fValC, blC, fValA, blA, fValB, blB); }, [](TMultivectorC &wC, const typename TMultivectorC::TValue &fValC, const typename TMultivectorC::TBlade &blC)
					{ wC.AddValueBlade(fValC, blC); }, [](TMultivectorC &wX)
					{ Reverse(wX); }, [](const typename TMultivectorC::TBlade &blX) -> unsigned
					{ return blX.GetReverseSign(); });
		}

		template <typename TMultivectorC, typename TMultivectorA, typename TMultivectorB>
		void OP_Conjugate(TMultivectorC &wC, const TMultivectorA &wA, const bool bConjugateA, const TMultivectorB &wB, const bool bConjugateB)
		{
			Product(wC, wA, bConjugateA, wB, bConjugateB, [](typename TMultivectorC::TValue &fValC, typename TMultivectorC::TBlade &blC, const typename TMultivectorA::TValue &fValA, const typename TMultivectorA::TBlade &blA, const typename TMultivectorB::TValue &fValB, const typename TMultivectorB::TBlade &blB) -> bool
					{ return GA::OP(fValC, blC, fValA, blA, fValB, blB); }, [](TMultivectorC &wC, const typename TMultivectorC::TValue &fValC, const typename TMultivectorC::TBlade &blC)
					{ wC.AddValueBlade(fValC, blC); }, [](TMultivectorC &wX)
					{ Conjugate(wX); }, [](const typename TMultivectorC::TBlade &blX) -> unsigned
					{ return blX.GetConjugateSign(); });
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Versor product.
		/// </summary>
		///
		/// <typeparam name="typename TMultivectorC">	Type of the typename t multivector c. </typeparam>
		/// <typeparam name="typename TMultivectorA">	Type of the typename t multivector a. </typeparam>
		/// <typeparam name="typename TMultivectorB">	Type of the typename t multivector b. </typeparam>
		/// <param name="wC">	  	[in,out] The w c. </param>
		/// <param name="wVersor">	The versor. </param>
		/// <param name="wB">	  	The w b. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TMultivectorC, typename TMultivectorA, typename TMultivectorB>
		void VersorProduct(TMultivectorC &wC, const TMultivectorA &wVersor, const TMultivectorB &wB)
		{
			try
			{
				TMultivectorC wX(wVersor.GetValuePrecision());

				GA::GP(wX, wVersor, wB);
				GA::GP_Reverse(wC, wX, false, wVersor, true);
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error calculating versor product", xEx);
			}
		}

		template <typename TMultivectorC, typename TMultivectorA, typename TMultivectorB>
		void VersorProduct(std::vector<TMultivectorC> &vecwC, const TMultivectorA &wVersor, const std::vector<TMultivectorB> &vecwB)
		{
			try
			{
				TMultivectorC wX(wVersor.GetValuePrecision());
				vecwC.resize(vecwB.size());

				ForEachIndex(vecwB, [&](const TMultivectorB &wB, size_t uIndex)
							 {
							GA::GP(wX, wVersor, wB);
							GA::GP_Reverse(vecwC[uIndex], wX, false, wVersor, true); });
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error calculating versor product", xEx);
			}
		}

		template <typename TValue, typename TMultivectorA, typename TMultivectorB>
		void SP(TValue &fValue, const TMultivectorA &wA, const TMultivectorB &wB)
		{
			fValue = TValue(0);

			wA.ForEachBlade([&](const typename TMultivectorA::TValue &fValA, const typename TMultivectorA::TBlade &blA)
							{ ScalarProductOperator(fValue, fValA, blA, wB); });
		}

		template <typename TValue, typename TValueA, typename TBladeA, typename TMultivectorB>
		void ScalarProductOperator(TValue &fValue, const TValueA &fValA, const TBladeA &blA, const TMultivectorB &wB)
		{
			typename TMultivectorB::TValue fValB;
			typename TMultivectorB::TBlade blB;

			if (wB.GetValueBlade(fValB, blA))
			{
				if (blA.GetConjugateSign() != 0)
				{
					fValue -= fValA * fValB;
				}
				else
				{
					fValue += fValA * fValB;
				}
			}
		}

		template <typename TMultivector>
		TMultivector GetReverse(const TMultivector &wB)
		{
			typedef typename TMultivector::TValue TValue;
			typedef typename TMultivector::TBlade TBlade;
			try
			{
				TMultivector wA(wB);

				Reverse(wA);
				return wA;
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error reversing multivector", xEx);
			}
		}

		template <typename TMultivector>
		void Reverse(TMultivector &wA)
		{
			typedef typename TMultivector::TValue TValue;
			typedef typename TMultivector::TBlade TBlade;

			wA.ForEachBlade([&](TValue &fValA, const TBlade &blA)
							{
						const unsigned uSign = blA.GetReverseSign();

						if ((uSign & 1) != 0)
						{
							fValA = -fValA;
						} });
		}

		template <typename TMultivector>
		TMultivector GetConjugate(const TMultivector &wB)
		{
			typedef typename TMultivector::TValue TValue;
			typedef typename TMultivector::TBlade TBlade;
			try
			{
				TMultivector wA(wB);

				Conjugate(wA);
				return wA;
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error conjugating multivector", xEx);
			}
		}

		template <typename TMultivector>
		void Conjugate(TMultivector &wA)
		{
			typedef typename TMultivector::TValue TValue;
			typedef typename TMultivector::TBlade TBlade;

			wA.ForEachBlade([&](TValue &fValA, const TBlade &blA)
							{
						const unsigned uSign = blA.GetConjugateSign();

						if ((uSign & 1) != 0)
						{
							fValA = -fValA;
						} });
		}

		template <typename TMultivector, typename TCongruence>
		TMultivector GetCongruence(const TMultivector &wB, const TCongruence &xCongruence)
		{
			typedef typename TMultivector::TValue TValue;
			typedef typename TMultivector::TBlade TBlade;

			try
			{
				TMultivector wA(wB);

				if (!Congruence(wA, xCongruence))
				{
					TAN_THROW_RT("Error applying congruence to multivector");
				}

				return wA;
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error in evaluating congruence of multivector", xEx);
			}
		}

		template <typename TMultivector, typename TCongruence>
		bool Congruence(TMultivector &wA, const TCongruence &xCongruence)
		{
			typedef typename TMultivector::TValue TValue;
			typedef typename TMultivector::TBlade TBlade;

			return wA.ForEachBladeTest([&](TValue &fValA, const TBlade &blA) -> bool
									   {
						TValue fValB = fValA;
						return xCongruence.Map(fValA, fValB); });
		}

		template <typename TMultivector, typename TCongruence>
		TMultivector GetInverseCongruence(const TMultivector &wB, const TCongruence &xCongruence)
		{
			typedef typename TMultivector::TValue TValue;
			typedef typename TMultivector::TBlade TBlade;

			try
			{
				TMultivector wA(wB);

				if (!InverseCongruence(wA, xCongruence))
				{
					TAN_THROW_RT("Error evaluating inverse congruence to multivector");
				}

				return wA;
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error in evaluating inverse congruence of multivector", xEx);
			}
		}

		template <typename TMultivector, typename TCongruence>
		bool InverseCongruence(TMultivector &wA, const TCongruence &xCongruence)
		{
			typedef typename TMultivector::TValue TValue;
			typedef typename TMultivector::TBlade TBlade;

			return wA.ForEachBladeTest([&](TValue &fValA, const TBlade &blA) -> bool
									   {
						TValue fValB = fValA;
						return xCongruence.InvMap(fValA, fValB); });
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Compute the unsigned complement of a multivector.
		///
		/// 	Each blade is mapped to its bitwise complement within the algebra
		/// 	(blade_id XOR pseudoscalar_id), with no coefficient sign changes.
		///
		/// 	This is an involution: Complement(Complement(A)) = A for all
		/// 	dimensions and signatures.
		///
		/// 	This is a purely combinatorial operation, NOT the Clifford dual.
		/// 	Use Dual() for the geometrically correct dual ★A = A · I⁻¹.
		/// </summary>
		///
		/// <typeparam name="TMultivectorA">Source multivector type.</typeparam>
		/// <typeparam name="TMultivectorB">Destination multivector type.</typeparam>
		/// <param name="wB">[out] Result multivector.</param>
		/// <param name="wA">The input multivector.</param>
		///
		/// <returns>Reference to wB.</returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TMultivectorA, typename TMultivectorB>
		TMultivectorB &Complement(TMultivectorB &wB, const TMultivectorA &wA)
		{
			typedef typename TMultivectorA::TValue TValue;
			typedef typename TMultivectorA::TBlade TBlade;

			wB.SetValuePrecision(wA.GetValuePrecision());
			wB.Reset();

			TBlade blB;
			TValue fValB;

			wA.ForEachBlade([&](const TValue &fValA, const TBlade &blA)
							{
						fValB = fValA;
						blA.GetComplement(fValB, blB);
						wB.SetValueBlade(fValB, blB); });

			return wB;
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Compute the signed dual ★A = A · I⁻¹ of a multivector.
		///
		/// 	Each blade is mapped to its bitwise complement and the coefficient
		/// 	sign is adjusted according to the geometric product with the inverse
		/// 	pseudoscalar.
		///
		/// 	The dual-of-dual may introduce a sign change depending on dimension
		/// 	and signature: ★★A = (−1)^(D(D−1)/2 + s) · A.
		///
		/// 	Use Complement() for the unsigned complement that is involutive for
		/// 	all dimensions and signatures.
		/// </summary>
		///
		/// <typeparam name="TMultivectorA">Source multivector type.</typeparam>
		/// <typeparam name="TMultivectorB">Destination multivector type.</typeparam>
		/// <param name="wB">[out] Result multivector.</param>
		/// <param name="wA">The input multivector.</param>
		///
		/// <returns>Reference to wB.</returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TMultivectorA, typename TMultivectorB>
		TMultivectorB &Dual(TMultivectorB &wB, const TMultivectorA &wA)
		{
			typedef typename TMultivectorA::TValue TValue;
			typedef typename TMultivectorA::TBlade TBlade;

			wB.SetValuePrecision(wA.GetValuePrecision());
			wB.Reset();

			TBlade blB;
			TValue fValB;

			wA.ForEachBlade([&](const TValue &fValA, const TBlade &blA)
							{
						fValB = fValA;
						blA.GetDual(fValB, blB);
						wB.SetValueBlade(fValB, blB); });

			return wB;
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Compute the left dual I · A of a multivector.
		///
		/// 	Each blade is left-multiplied by the pseudoscalar I.  The blade
		/// 	mask is the bitwise complement and the coefficient sign accounts
		/// 	for the geometric product with I (no inverse needed).
		///
		/// 	This is the counterpart to Dual(A) = A · I⁺.  For invertible
		/// 	pseudoscalars (e.g. G(3,0)): LDual(A) = (−1)^k · Dual(A) for
		/// 	grade-k elements.  For non-invertible pseudoscalars (e.g. PGA),
		/// 	LDual is simpler since it uses I directly without needing a
		/// 	pseudoinverse.
		/// </summary>
		///
		/// <typeparam name="TMultivectorA">Source multivector type.</typeparam>
		/// <typeparam name="TMultivectorB">Destination multivector type.</typeparam>
		/// <param name="wB">[out] Result multivector.</param>
		/// <param name="wA">The input multivector.</param>
		///
		/// <returns>Reference to wB.</returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TMultivectorA, typename TMultivectorB>
		TMultivectorB &LDual(TMultivectorB &wB, const TMultivectorA &wA)
		{
			typedef typename TMultivectorA::TValue TValue;
			typedef typename TMultivectorA::TBlade TBlade;

			wB.SetValuePrecision(wA.GetValuePrecision());
			wB.Reset();

			TBlade blB;
			TValue fValB;

			wA.ForEachBlade([&](const TValue &fValA, const TBlade &blA)
							{
						fValB = fValA;
						blA.GetLeftDual(fValB, blB);
						wB.SetValueBlade(fValB, blB); });

			return wB;
		}

		template <typename TMultivector>
		TMultivector GetGradeProjection(const TMultivector &wB, unsigned uGrade)
		{
			typedef typename TMultivector::TValue TValue;
			typedef typename TMultivector::TBlade TBlade;
			try
			{
				TMultivector wA(wB.GetValuePrecision());
				wB.ForEachBlade([&](const TValue &fValB, const TBlade &blB)
								{
							unsigned uBladeGrade;
							blB.GetGrade(uBladeGrade);

							if (uBladeGrade == uGrade)
							{
								wA.SetValueBlade(fValB, blB);
							} });

				return wA;
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error getting grade projection", xEx);
			}
		}

		template <typename TMultivector>
		void GradeProjection(TMultivector &wA, unsigned uGrade)
		{
			typedef typename TMultivector::TValue TValue;
			typedef typename TMultivector::TBlade TBlade;

			wA.ForEachBlade([&](TValue &fValA, const TBlade &blA)
							{
						unsigned uBladeGrade;
						blA.GetGrade(uBladeGrade);

						if (uBladeGrade != uGrade)
						{
							fValA = TValue(0);
						} });
		}

		template <typename TMultivector>
		typename TMultivector::TValue GreatestCommonDenominator(const TMultivector &wA)
		{
			typedef typename TMultivector::TValue TValue;
			typedef typename TMultivector::TBlade TBlade;

			TValue fValX = TValue(0);

			wA.ForEachBladeIndexTest([&](const TValue &fValA, const TBlade &blA, unsigned uIdx) -> bool
									 {
						if (uIdx == 0)
						{
							fValX = fValA;
						}
						else
						{
							fValX = gcd(fValA, fValX);
							if (fValX == TValue(1))
							{
								// There will be no smaller GCD than 1. So break the loop.
								return false;
							}
						}
						return true; });

			return fValX;
		}

		template <typename TMultivector>
		typename TMultivector::TValue MagnitudeSquared(const TMultivector &wA)
		{
			typedef typename TMultivector::TValue TValue;
			typedef typename TMultivector::TBlade TBlade;

			TValue fSumSquared = TValue(0);

			wA.ForEachBlade([&](const TValue &fValA, const TBlade &blA)
							{ fSumSquared += fValA * fValA; });

			return fSumSquared;
		}

		template <typename TMultivector>
		typename TMultivector::TValue Magnitude(const TMultivector &wA)
		{
			typedef typename TMultivector::TValue TValue;

			double fMagnitude = double(MagnitudeSquared(wA));
			return TValue(::sqrt(fMagnitude));
		}

		template <typename TMultivector>
		typename TMultivector::TValue Scalar(const TMultivector &wA)
		{
			typedef typename TMultivector::TValue TValue;
			typedef typename TMultivector::TBlade TBlade;

			TValue fScalar = TValue(0);

			wA.ForEachBladeTest([&](const TValue &fValA, const TBlade &blA) -> bool
								{
						if (blA.GetId() == 0)
						{
							fScalar = fValA;
							return false;	// end loop
						}

						return true; });

			return fScalar;
		}

		template <typename TMultivector>
		bool IsScalar(const TMultivector &wA)
		{
			typedef typename TMultivector::TValue TValue;
			typedef typename TMultivector::TBlade TBlade;

			bool bIsScalar = wA.ForEachBladeTest([&](const TValue &fValA, const TBlade &blA) -> bool
												 {
						if (!wA.IsZero(fValA) && (blA.GetId() != 0))
						{
							return false;
						}
						else
						{
							return true;
						} });

			return bIsScalar;
		}

		template <typename TMultivector>
		std::vector<unsigned> Grades(const TMultivector &wA)
		{
			typedef typename TMultivector::TValue TValue;
			typedef typename TMultivector::TBlade TBlade;

			std::vector<unsigned> vecGrades;

			wA.ForEachBlade([&](const TValue &fValA, const TBlade &blA)
							{
						if (!wA.IsZero(fValA))
						{
							unsigned uGrade;
							blA.GetGrade(uGrade);
							vecGrades.push_back(uGrade);
						} });

			// Deduplicate and sort
			std::sort(vecGrades.begin(), vecGrades.end());
			vecGrades.erase(std::unique(vecGrades.begin(), vecGrades.end()), vecGrades.end());
			return vecGrades;
		}

		template <typename TMultivector>
		bool IsGrade(const TMultivector &wA, unsigned uExpectedGrade)
		{
			typedef typename TMultivector::TValue TValue;
			typedef typename TMultivector::TBlade TBlade;

			bool bAllMatch = wA.ForEachBladeTest([&](const TValue &fValA, const TBlade &blA) -> bool
												 {
						if (!wA.IsZero(fValA))
						{
							unsigned uGrade;
							blA.GetGrade(uGrade);
							if (uGrade != uExpectedGrade)
								return false;
						}
						return true; });

			return bAllMatch;
		}

		template <typename TMultivector>
		bool IsZero(const TMultivector &wA)
		{
			typedef typename TMultivector::TValue TValue;
			typedef typename TMultivector::TBlade TBlade;

			bool bIsZero = wA.ForEachBladeTest([&](const TValue &fValA, const TBlade &blA) -> bool
											   {
						if (!wA.IsZero(fValA))
						{
							return false;
						}
						else
						{
							return true;
						} });

			return bIsZero;
		}

		template <typename TMultivectorA, typename TMultivectorB>
		void ProjectOnto(TMultivectorA &wA, const TMultivectorB &wB)
		{
			typedef typename TMultivectorA::TValue TValue;
			typedef typename TMultivectorA::TBlade TBlade;

			wA.ForEachBlade([&](TValue &fValA, const TBlade &blA)
							{
								typename TMultivectorB::TValue fValB;
								if (!wB.GetValueBlade(fValB, blA))
								{
									fValA = TValue(0);
								}
							});
		}

		template <typename TMultivectorA>
		void ProjectOnto(TMultivectorA &wA,
						 const GA::CBladeMask<typename TMultivectorA::TBlade> &xMask)
		{
			typedef typename TMultivectorA::TValue TValue;
			typedef typename TMultivectorA::TBlade TBlade;

			wA.ForEachBlade([&](TValue &fValA, const TBlade &blA)
							{
								if (!xMask.Contains(blA))
								{
									fValA = TValue(0);
								}
							});
		}

		template <typename TMultivectorA, typename TMultivectorB>
		void ConvertMultivectorType(TMultivectorA &wA, const TMultivectorB &wB)
		{
			wA.Zero();
			wA.SetValuePrecision(wB.GetValuePrecision());

			wB.ForEachBlade([&](const typename TMultivectorB::TValue &fValB, const typename TMultivectorB::TBlade &blB)
							{
						if (!wA.SetValueBlade(fValB, blB))
						{
							TAN_THROW_RT("Error converting multivector");
						} });
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Adds wC. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="wC">	The mv c. </param>
		/// <param name="wA">	The mv a. </param>
		/// <param name="wB">	The mv b. </param>
		///
		/// <returns>	. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		template <typename TMultivectorA, typename TMultivectorB, typename TMultivectorC>
		TMultivectorC &Add(TMultivectorC &wC, const TMultivectorA &wA, const TMultivectorB &wB)
		{
			wC = wA;
			wC += wB;
			return wC;
		}

		////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Subs. </summary>
		///
		/// <remarks>	Perwass, . </remarks>
		///
		/// <param name="wC">	The mv c. </param>
		/// <param name="wA">	The mv a. </param>
		/// <param name="wB">	The mv b. </param>
		///
		/// <returns>	. </returns>
		////////////////////////////////////////////////////////////////////////////////////////////////////

		template <typename TMultivectorA, typename TMultivectorB, typename TMultivectorC>
		TMultivectorC &Sub(TMultivectorC &wC, const TMultivectorA &wA, const TMultivectorB &wB)
		{
			wC = wA;
			wC -= wB;
			return wC;
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Addition operator. </summary>
		///
		/// <typeparam name="TValue">						   	Type of the value. </typeparam>
		/// <typeparam name="unsigned t_uVectorSpaceDimension">	Type of the unsigned t u vector space dimension. </typeparam>
		/// <typeparam name="unsigned t_uVectorSpaceSignature">	Type of the unsigned t u vector space signature. </typeparam>
		/// <param name="wA">	The mv a. </param>
		/// <param name="wB">	The mv b. </param>
		///
		/// <returns>	The result of the operation. </returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TMultivector,
				  typename = typename TMultivector::TValue,
				  typename = typename TMultivector::TBlade>
		TMultivector operator+(const TMultivector &wA, const TMultivector &wB)
		{
			try
			{
				TMultivector wC(wA);
				wC += wB;
				return wC;
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error adding multivectors", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Subtraction operator. </summary>
		///
		/// <typeparam name="TValue">						   	Type of the value. </typeparam>
		/// <typeparam name="unsigned t_uVectorSpaceDimension">	Type of the unsigned t u vector space dimension. </typeparam>
		/// <typeparam name="unsigned t_uVectorSpaceSignature">	Type of the unsigned t u vector space signature. </typeparam>
		/// <param name="wA">	The mv a. </param>
		/// <param name="wB">	The mv b. </param>
		///
		/// <returns>	The result of the operation. </returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TMultivector,
				  typename = typename TMultivector::TValue,
				  typename = typename TMultivector::TBlade>
		TMultivector operator-(const TMultivector &wA, const TMultivector &wB)
		{
			try
			{
				TMultivector wC(wA);
				wC -= wB;
				return wC;
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error substracting multivectors", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Addition operator. </summary>
		///
		/// <typeparam name="TValue">						   	Type of the value. </typeparam>
		/// <typeparam name="unsigned t_uVectorSpaceDimension">	Type of the unsigned t u vector space dimension. </typeparam>
		/// <typeparam name="unsigned t_uVectorSpaceSignature">	Type of the unsigned t u vector space signature. </typeparam>
		/// <typeparam name="unsigned t_uSubspaceDimension">   	Type of the unsigned t u subspace dimension. </typeparam>
		/// <param name="wA">	The mv a. </param>
		/// <param name="wB">	The mv b. </param>
		///
		/// <returns>	The result of the operation. </returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TValue, typename TBlade, unsigned t_uSubspaceDimensionA, unsigned t_uSubspaceDimensionB>
		_CMultivector<TValue, TBlade> operator+(const _CSubspaceMultivector<TValue, TBlade, t_uSubspaceDimensionA> &wA,
												const _CSubspaceMultivector<TValue, TBlade, t_uSubspaceDimensionB> &wB)
		{
			try
			{
				_CMultivector<TValue, TBlade> wC(wA);
				wC += wB;
				return wC;
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error adding multivectors", xEx);
			}
		}

		template <typename TValue, typename TBlade, unsigned t_uSubspaceDimension>
		_CMultivector<TValue, TBlade> operator+(const _CMultivector<TValue, TBlade> &wA, const _CSubspaceMultivector<TValue, TBlade, t_uSubspaceDimension> &wB)
		{
			try
			{
				_CMultivector<TValue, TBlade> wC(wA);
				wC += wB;
				return wC;
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error adding multivectors", xEx);
			}
		}

		template <typename TValue, typename TBlade, unsigned t_uSubspaceDimension>
		_CMultivector<TValue, TBlade> operator+(const _CSubspaceMultivector<TValue, TBlade, t_uSubspaceDimension> &wA, const _CMultivector<TValue, TBlade> &wB)
		{
			try
			{
				_CMultivector<TValue, TBlade> wC(wA);
				wC += wB;
				return wC;
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error adding multivectors", xEx);
			}
		}

		template <typename TValue, typename TBlade>
		_CMultivector<TValue, TBlade> operator+(const _CMultivector<TValue, TBlade> &wA, const CDynamicMultivector<TValue, TBlade> &wB)
		{
			try
			{
				_CMultivector<TValue, TBlade> wC(wA);
				wC += wB;
				return wC;
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error adding multivectors", xEx);
			}
		}

		template <typename TValue, typename TBlade>
		_CMultivector<TValue, TBlade> operator+(const CDynamicMultivector<TValue, TBlade> &wA, const _CMultivector<TValue, TBlade> &wB)
		{
			try
			{
				_CMultivector<TValue, TBlade> wC(wA);
				wC += wB;
				return wC;
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error adding multivectors", xEx);
			}
		}

		template <typename TValue, typename TBlade, unsigned t_uSubspaceDimension>
		CDynamicMultivector<TValue, TBlade> operator+(const CDynamicMultivector<TValue, TBlade> &wA,
													  const _CSubspaceMultivector<TValue, TBlade, t_uSubspaceDimension> &wB)
		{
			try
			{
				CDynamicMultivector<TValue, TBlade> wC(wA);
				wC += wB;
				return wC;
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error adding multivectors", xEx);
			}
		}

		template <typename TValue, typename TBlade, unsigned t_uSubspaceDimension>
		CDynamicMultivector<TValue, TBlade> operator+(const _CSubspaceMultivector<TValue, TBlade, t_uSubspaceDimension> &wA,
													  const CDynamicMultivector<TValue, TBlade> &wB)
		{
			try
			{
				CDynamicMultivector<TValue, TBlade> wC(wA);
				wC += wB;
				return wC;
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error adding multivectors", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Subtraction operator. </summary>
		///
		/// <typeparam name="TValue">						   	Type of the value. </typeparam>
		/// <typeparam name="unsigned t_uVectorSpaceDimension">	Type of the unsigned t u vector space dimension. </typeparam>
		/// <typeparam name="unsigned t_uVectorSpaceSignature">	Type of the unsigned t u vector space signature. </typeparam>
		/// <typeparam name="unsigned t_uSubspaceDimension">   	Type of the unsigned t u subspace dimension. </typeparam>
		/// <param name="wA">	The mv a. </param>
		/// <param name="wB">	The mv b. </param>
		///
		/// <returns>	The result of the operation. </returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TValue, typename TBlade, unsigned t_uSubspaceDimensionA, unsigned t_uSubspaceDimensionB>
		_CMultivector<TValue, TBlade> operator-(const _CSubspaceMultivector<TValue, TBlade, t_uSubspaceDimensionA> &wA,
												const _CSubspaceMultivector<TValue, TBlade, t_uSubspaceDimensionB> &wB)
		{
			try
			{
				_CMultivector<TValue, TBlade> wC(wA);
				wC -= wB;
				return wC;
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error subtracting multivectors", xEx);
			}
		}

		template <typename TValue, typename TBlade, unsigned t_uSubspaceDimension>
		_CMultivector<TValue, TBlade> operator-(const _CMultivector<TValue, TBlade> &wA, const _CSubspaceMultivector<TValue, TBlade, t_uSubspaceDimension> &wB)
		{
			try
			{
				_CMultivector<TValue, TBlade> wC(wA);
				wC -= wB;
				return wC;
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error subtracting multivectors", xEx);
			}
		}

		template <typename TValue, typename TBlade, unsigned t_uSubspaceDimension>
		_CMultivector<TValue, TBlade> operator-(const _CSubspaceMultivector<TValue, TBlade, t_uSubspaceDimension> &wA, const _CMultivector<TValue, TBlade> &wB)
		{
			try
			{
				_CMultivector<TValue, TBlade> wC(wA);
				wC -= wB;
				return wC;
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error subtracting multivectors", xEx);
			}
		}

		template <typename TValue, typename TBlade>
		_CMultivector<TValue, TBlade> operator-(const _CMultivector<TValue, TBlade> &wA, const CDynamicMultivector<TValue, TBlade> &wB)
		{
			try
			{
				_CMultivector<TValue, TBlade> wC(wA);
				wC -= wB;
				return wC;
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error subtracting multivectors", xEx);
			}
		}

		template <typename TValue, typename TBlade>
		_CMultivector<TValue, TBlade> operator-(const CDynamicMultivector<TValue, TBlade> &wA, const _CMultivector<TValue, TBlade> &wB)
		{
			try
			{
				_CMultivector<TValue, TBlade> wC(wA);
				wC -= wB;
				return wC;
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error subtracting multivectors", xEx);
			}
		}

		template <typename TValue, typename TBlade, unsigned t_uSubspaceDimension>
		CDynamicMultivector<TValue, TBlade> operator-(const CDynamicMultivector<TValue, TBlade> &wA,
													  const _CSubspaceMultivector<TValue, TBlade, t_uSubspaceDimension> &wB)
		{
			try
			{
				CDynamicMultivector<TValue, TBlade> wC(wA);
				wC -= wB;
				return wC;
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error subtracting multivectors", xEx);
			}
		}

		template <typename TValue, typename TBlade, unsigned t_uSubspaceDimension>
		CDynamicMultivector<TValue, TBlade> operator-(const _CSubspaceMultivector<TValue, TBlade, t_uSubspaceDimension> &wA,
													  const CDynamicMultivector<TValue, TBlade> &wB)
		{
			try
			{
				CDynamicMultivector<TValue, TBlade> wC(wA);
				wC -= wB;
				return wC;
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error subtracting multivectors", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Multiplication operator. </summary>
		///
		/// <typeparam name="TValue">						   	Type of the value. </typeparam>
		/// <typeparam name="unsigned t_uVectorSpaceDimension">	Type of the unsigned t u vector space dimension. </typeparam>
		/// <typeparam name="unsigned t_uVectorSpaceSignature">	Type of the unsigned t u vector space signature. </typeparam>
		/// <param name="wA">   	The mv a. </param>
		/// <param name="fValue">	The value. </param>
		///
		/// <returns>	The result of the operation. </returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TMultivector>
		TMultivector operator*(const TMultivector &wA, const typename TMultivector::TValue &fValue)
		{
			try
			{
				TMultivector wC(wA);
				wC *= fValue;
				return wC;
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error evaluating product of multivector with scalar", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Multiplication operator. </summary>
		///
		/// <typeparam name="TValue">						   	Type of the value. </typeparam>
		/// <typeparam name="unsigned t_uVectorSpaceDimension">	Type of the unsigned t u vector space dimension. </typeparam>
		/// <typeparam name="unsigned t_uVectorSpaceSignature">	Type of the unsigned t u vector space signature. </typeparam>
		/// <param name="fValue">	The value. </param>
		/// <param name="wA">   	The mv a. </param>
		///
		/// <returns>	The result of the operation. </returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TMultivector>
		TMultivector operator*(const typename TMultivector::TValue &fValue, const TMultivector &wA)
		{
			try
			{
				TMultivector wC(wA);
				wC *= fValue;
				return wC;
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error evaluating product of scalar with multivector", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>	Division operator. </summary>
		///
		/// <typeparam name="TValue">						   	Type of the value. </typeparam>
		/// <typeparam name="unsigned t_uVectorSpaceDimension">	Type of the unsigned t u vector space dimension. </typeparam>
		/// <typeparam name="unsigned t_uVectorSpaceSignature">	Type of the unsigned t u vector space signature. </typeparam>
		/// <param name="wA">   	The mv a. </param>
		/// <param name="fValue">	The value. </param>
		///
		/// <returns>	The result of the operation. </returns>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TMultivector>
		TMultivector operator/(const TMultivector &wA, const typename TMultivector::TValue &fValue)
		{
			try
			{
				TMultivector wC(wA);
				wC /= fValue;
				return wC;
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error evaluating division of multivector by scalar", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// \brief
		/// 	Modulus operator
		///
		/// \tparam	TMultivector Type of the multivector.
		/// \param	wA	  	The w a.
		/// \param	fValue	The value.
		///
		/// \return The result of the operation.
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template <typename TMultivector>
		TMultivector operator%(const TMultivector &wA, const typename TMultivector::TValue &fValue)
		{
			try
			{
				TMultivector wC(wA);
				wC %= fValue;
				return wC;
			}
			catch (std::exception &xEx)
			{
				TAN_RETHROW("Error evaluating modulus of multivector", xEx);
			}
		}
	}
} // .GA
