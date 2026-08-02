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

#include <map>

#include "Tan.Math/Matrix.h"

#include "Multivector.h"
#include "DynamicMultivector.h"
#include "BladeMask.h"
#include "SubspaceBasis.h"
#include "SubspaceMask.h"

namespace Tan
{
	namespace GA
	{
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Eval blade mask.
		/// </summary>
		///
		/// <typeparam name="typename TValue">	Type of the typename t value. </typeparam>
		/// <typeparam name="typename TBlade">	Type of the typename t blade. </typeparam>
		/// <param name="xBladeMask">	[in,out] The blade mask. </param>
		/// <param name="xSubspace"> 	The subspace. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TValue, typename TBlade>
		void EvalBladeMask(CBladeMask<TBlade>& xBladeMask, const CSubspaceBasis<TValue, TBlade>& xSubspace)
		{
			typedef typename CSubspaceBasis<TValue, TBlade>::TMultivector TMultivector;

			xBladeMask.Reset();

			xSubspace.ForEachBasisBlade([&](const TMultivector& wBlade, const TMultivector& wRecipBlade)
					{
						_EvalBladeMask_InnerLoop(xBladeMask, wBlade);
					});
		}

		template<typename TMultivector>
		void _EvalBladeMask_InnerLoop(CBladeMask<typename TMultivector::TBlade>& xBladeMask, const TMultivector& wBlade)
		{
			wBlade.ForEachBlade([&](const typename TMultivector::TValue& fValA, const typename TMultivector::TBlade& blA)
					{
						if (!wBlade.IsZero(fValA))
						{
							xBladeMask.Insert(blA);
						}
					});
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Eval blade list.
		/// </summary>
		///
		/// <typeparam name="typename TValue">   	Type of the typename t value. </typeparam>
		/// <typeparam name="typename TBlade">   	Type of the typename t blade. </typeparam>
		/// <typeparam name="size_t t_uVecDim">	Type of the size_t t u vector dim. </typeparam>
		/// <param name="vBladeList">	[in,out] List of blades. </param>
		/// <param name="xSubspace"> 	The subspace. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TValue, typename TBlade, int t_uVecDim>
		void EvalBladeList(tvec<TBlade, t_uVecDim>& vBladeList, const CSubspaceBasis<TValue, TBlade>& xSubspace)
		{
			typedef typename CSubspaceBasis<TValue, TBlade>::TMultivector TMultivector;

			CBladeMask<TBlade> xBladeMask;
			EvalBladeMask(xBladeMask, xSubspace);

			const size_t uBladeMaskDim = xBladeMask.Count();
			if (uBladeMaskDim != t_uVecDim)
			{
				TAN_THROW_RT("Subspace and vector dimensions are not equal");
			}

			xBladeMask.ForEachBlade([&](size_t uBitIdx, const TBlade& blA)
					{
						vBladeList[uBitIdx] = blA;
					});
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Eval product blade mask.
		/// </summary>
		///
		/// <typeparam name="typename TMultivector">	Type of the typename t multivector. </typeparam>
		/// <typeparam name="typename FuncOp">			Type of the typename function operation. </typeparam>
		/// <param name="xMaskC">	   	[in,out] The mask c. </param>
		/// <param name="wA">		   	The mv a. </param>
		/// <param name="xMaskB">	   	The mask b. </param>
		/// <param name="bLeftToRight">	true to left to right. </param>
		/// <param name="xFuncOp">	   	The function operation. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TSubspaceBasis, typename TStyle, typename FuncOp>
		void _EvalProductSubspaceMask(CSubspaceMask<TSubspaceBasis>& xMaskC,
				const CSubspaceMask<TSubspaceBasis>& xMaskA,
				const CSubspaceMask<TSubspaceBasis>& xMaskB,
				const TStyle& xAlgebraBasis,
				FuncOp xFuncOp)
		{
			typedef typename TSubspaceBasis::TMultivector TMultivector;

			// Find all possible result blades
			xMaskC.Reset();

			xMaskA.ForEachBasisBladePair(xAlgebraBasis, [&](size_t uBitIdxA, const TMultivector& wBladeA, const TMultivector& wRecipBladeA)
					{
						_EvalProductSubspaceMask_InnerLoop(xMaskC, wBladeA, xMaskB, xAlgebraBasis, xFuncOp);
					});
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Eval product blade mask inner loop.
		/// </summary>
		///
		/// <typeparam name="typename TBlade">	Type of the typename t blade. </typeparam>
		/// <typeparam name="typename FuncOp">	Type of the typename function operation. </typeparam>
		/// <param name="xMaskC">	   	[in,out] The mask c. </param>
		/// <param name="blA">		   	The bl a. </param>
		/// <param name="xMaskB">	   	The mask b. </param>
		/// <param name="bLeftToRight">	true to left to right. </param>
		/// <param name="xFuncOp">	   	The function operation. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TSubspaceBasis, typename TStyle, typename FuncOp>
		void _EvalProductSubspaceMask_InnerLoop(CSubspaceMask<TSubspaceBasis>& xMaskC,
				const typename TSubspaceBasis::TMultivector& wBladeA,
				const CSubspaceMask<TSubspaceBasis>& xMaskB,
				const TStyle& xAlgebraBasis,
				FuncOp xFuncOp)
		{
			typedef typename TSubspaceBasis::TMultivector TMultivector;
			TMultivector wBladeC;

			xMaskB.ForEachBasisBladePair((const TSubspaceBasis&) xAlgebraBasis, [&](size_t uBitIdxB, const TMultivector& wBladeB, const TMultivector& wRecipBladeB)
					{
						xFuncOp(wBladeC, wBladeA, wBladeB);
						//printf("------\n(%s) * (%s) = (%s)\n",
						//	xAlgebraBasis.ToString(wBladeA).c_str(), xAlgebraBasis.ToString(wBladeB).c_str(), xAlgebraBasis.ToString(wBladeC).c_str());

						xMaskC.Insert(wBladeC, (const TSubspaceBasis&) xAlgebraBasis);
						//printf("%s\n", xAlgebraBasis.ToString(xMaskC, true).c_str());
					});
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Eval product blade mask gp.
		/// </summary>
		///
		/// <typeparam name="typename TMultivector">	Type of the typename t multivector. </typeparam>
		/// <param name="xMaskC">	   	[in,out] The mask c. </param>
		/// <param name="wA">		   	The mv a. </param>
		/// <param name="xMaskB">	   	The mask b. </param>
		/// <param name="bLeftToRight">	(optional) the left to right. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TSubspaceBasis, typename TStyle>
		void EvalProductSubspaceMask_GP(CSubspaceMask<TSubspaceBasis>& xMaskC,
				const CSubspaceMask<TSubspaceBasis>& xMaskA,
				const CSubspaceMask<TSubspaceBasis>& xMaskB,
				const TStyle& xAlgebraBasis)
		{
			typedef typename TSubspaceBasis::TMultivector TMultivector;

			_EvalProductSubspaceMask(xMaskC, xMaskA, xMaskB, xAlgebraBasis,
					[&](TMultivector& wC, const TMultivector& wA, const TMultivector& wB)
					{
						GA::GP(wC, wA, wB);
					});
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Eval product blade mask IP.
		/// </summary>
		///
		/// <typeparam name="typename TMultivector">	Type of the typename t multivector. </typeparam>
		/// <param name="xMaskC">	   	[in,out] The mask c. </param>
		/// <param name="wA">		   	The mv a. </param>
		/// <param name="xMaskB">	   	The mask b. </param>
		/// <param name="bLeftToRight">	(optional) the left to right. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TSubspaceBasis, typename TStyle>
		void EvalProductSubspaceMask_IP(CSubspaceMask<TSubspaceBasis>& xMaskC,
				const CSubspaceMask<TSubspaceBasis>& xMaskA,
				const CSubspaceMask<TSubspaceBasis>& xMaskB,
				const TStyle& xAlgebraBasis)
		{
			typedef typename TSubspaceBasis::TMultivector TMultivector;

			_EvalProductSubspaceMask(xMaskC, xMaskA, xMaskB, xAlgebraBasis,
					[&](TMultivector& wC, const TMultivector& wA, const TMultivector& wB)
					{
						GA::IP(wC, wA, wB);
					});
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Eval product blade mask operation.
		/// </summary>
		///
		/// <typeparam name="typename TMultivector">	Type of the typename t multivector. </typeparam>
		/// <param name="xMaskC">	   	[in,out] The mask c. </param>
		/// <param name="wA">		   	The mv a. </param>
		/// <param name="xMaskB">	   	The mask b. </param>
		/// <param name="bLeftToRight">	(optional) the left to right. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TSubspaceBasis, typename TStyle>
		void EvalProductSubspaceMask_OP(CSubspaceMask<TSubspaceBasis>& xMaskC,
				const CSubspaceMask<TSubspaceBasis>& xMaskA,
				const CSubspaceMask<TSubspaceBasis>& xMaskB,
				const TStyle& xAlgebraBasis)
		{
			typedef typename TSubspaceBasis::TMultivector TMultivector;

			_EvalProductSubspaceMask(xMaskC, xMaskA, xMaskB, xAlgebraBasis,
					[&](TMultivector& wC, const TMultivector& wA, const TMultivector& wB)
					{
						GA::OP(wC, wA, wB);
					});
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Convert multivector to matrix. The resultant matrix is a column vector that only contains those elements of wA that
		/// 	are non-zero. The list of non-zero blades in wA is returned in xMask in just that order in which the corresponding
		/// 	values are stored in the matrix.
		/// </summary>
		///
		/// <exception cref="std::exception">	Thrown when a C  error condition occurs. </exception>
		///
		/// <typeparam name="typename TMultivector">	Type of the typename t float. </typeparam>
		/// <param name="matA"> 	[in,out] The mat a. </param>
		/// <param name="wA">  	The mv a. </param>
		/// <param name="xMask">	The mask. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TSubspaceBasis, typename TMultivectorX>
		void ToMatrix(CMatrix<typename TSubspaceBasis::TValue>& matA, const TMultivectorX& wA, const GA::CSubspaceMask<TSubspaceBasis>& xMask, const TSubspaceBasis& xAlgebraBasis)
		{
			typedef typename TSubspaceBasis::TValue TValue;
			typedef typename TSubspaceBasis::TMultivector TMultivector;

			TValue fValA;
			size_t uDim = xMask.Count();

			if (uDim == 0)
			{
				TAN_THROW_RT("Empty Mask");
			}

			if (!wA.IsValid())
			{
				TAN_THROW_RT("Invalid input multivector");
			}

			matA.SetSize(uDim, 1);
			matA.Zero();

			xMask.ForEachBasisBladePair((const TSubspaceBasis&) xAlgebraBasis, [&](size_t uBitIdx, const TMultivector& wBlade, const TMultivector& wRecipBlade)
					{
						GA::SP(fValA, wA, wRecipBlade);
						matA(uBitIdx, 0) = fValA;
					});
		}

		template<typename TSubspaceBasis, typename TMultivectorX>
		void ToMatrix(CMatrix<typename TSubspaceBasis::TValue>& matA,
				const std::vector<TMultivectorX>& vecwListA,
				const GA::CSubspaceMask<TSubspaceBasis>& xMask,
				const TSubspaceBasis& xAlgebraBasis)
		{
			try
			{
				typedef typename TSubspaceBasis::TValue TValue;
				typedef typename TSubspaceBasis::TMultivector TMultivector;

				TValue fValA;
				const size_t uDim   = (size_t) xMask.Count();
				const size_t uMvCnt = (size_t) vecwListA.size();

				if (uMvCnt == 0)
				{
					TAN_THROW_RT("Empty multivector list");
				}

				if (uDim == 0)
				{
					TAN_THROW_RT("Empty Mask");
				}

				matA.SetSize(uDim, uMvCnt);
				matA.Zero();

				ForEachIndex(vecwListA, [&](const TMultivectorX& wA, size_t uMvIdx)
						{
							if (!wA.IsValid())
							{
								TAN_THROW_RT("Invalid input multivector");
							}

							xMask.ForEachBasisBladePair(xAlgebraBasis, [&](size_t uBitIdx, const TMultivector& wBlade, const TMultivector& wRecipBlade)
									{
										GA::SP(fValA, wA, wRecipBlade);
										matA(uBitIdx, uMvIdx) = fValA;
									});
						});
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error converting to matrix", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Convert to.
		/// </summary>
		///
		/// <exception cref="std::exception">	Thrown when a C  error condition occurs. </exception>
		///
		/// <typeparam name="typename TMultivector">	Type of the typename t multivector. </typeparam>
		/// <param name="wA">  	[in,out] The mv a. </param>
		/// <param name="matA"> 	The mat a. </param>
		/// <param name="xMask">	The mask. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TSubspaceBasis, typename TMultivectorX>
		void ToMultivector(TMultivectorX& wA,
				const CMatrix<typename TSubspaceBasis::TValue>& matA,
				const GA::CSubspaceMask<TSubspaceBasis>& xMask,
				const TSubspaceBasis& xAlgebraBasis)
		{
			try
			{
				typedef typename TSubspaceBasis::TValue TValue;
				typedef typename TSubspaceBasis::TMultivector TMultivector;

				TValue fValA;
				const size_t uMatRowCnt = (size_t) matA.GetRowCount();
				//const size_t uMatColCnt = (size_t)matA.GetColCount();

				if (uMatRowCnt != xMask.Count())
				{
					TAN_THROW_RT("Matrix row count is not equal to mask dimension.");
				}

				wA.Reset();
				if (!wA.IsValid())
				{
					TAN_THROW_RT("Invalid output multivector");
				}

				xMask.ForEachBasisBladePair(xAlgebraBasis, [&](size_t uBitIdx, const TMultivector& wBlade, const TMultivector& wRecipBlade)
						{
							fValA = matA(uBitIdx, 0);
							wA += fValA * wBlade;
						});
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error converting to multivector", xEx);
			}
		}

		template<typename TSubspaceBasis, typename TMultivectorX>
		void ToMultivector(std::vector<TMultivectorX>& vecwListA,
				const CMatrix<typename TSubspaceBasis::TValue>& matA,
				const GA::CSubspaceMask<TSubspaceBasis>& xMask,
				const TSubspaceBasis& xAlgebraBasis)
		{
			typedef typename TSubspaceBasis::TValue TValue;
			typedef typename TSubspaceBasis::TMultivector TMultivector;

			TValue fValA;
			try
			{
				const size_t uMatRowCnt = (size_t) matA.GetRowCount();
				const size_t uMatColCnt = (size_t) matA.GetColCount();
				const size_t uMaskCnt   = (size_t) xMask.Count();

				// Test whether each column in a matrix is a multivector
				if (uMatRowCnt == uMaskCnt)
				{
					vecwListA.resize(uMatColCnt);
					ForEachIndex(vecwListA, [&](TMultivectorX& wA, size_t uMvIdx)
							{
								wA.Reset();
								if (!wA.IsValid())
								{
									TAN_THROW_RT("Invalid output multivector");
								}

								xMask.ForEachBasisBladePair(xAlgebraBasis, [&](size_t uBitIdx, const TMultivector& wBlade, const TMultivector& wRecipBlade)
										{
											fValA = matA(uBitIdx, uMvIdx);
											wA += fValA * wBlade;
										});
							});
				}
				// Test whether multiple multivectors are stacked per column
				else if (uMatRowCnt % uMaskCnt == 0)
				{
					vecwListA.resize(uMatRowCnt / uMaskCnt);
					ForEachIndex(vecwListA, [&](TMultivectorX& wA, size_t uMvIdx)
							{
								const size_t uRowOffset = uMvIdx * uMaskCnt;

								wA.Reset();
								if (!wA.IsValid())
								{
									TAN_THROW_RT("Invalid output multivector");
								}

								xMask.ForEachBasisBladePair(xAlgebraBasis, [&](size_t uBitIdx, const TMultivector& wBlade, const TMultivector& wRecipBlade)
										{
											fValA = matA(uRowOffset + uBitIdx, 0);
											wA += fValA * wBlade;
										});
							});
				}
				// Otherwise we cannot map the matrix
				else
				{
					TAN_THROW_RT("Matrix dimensions are incompatible with mask");
				}
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error converting to multivector", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Eval geometric product matrix.
		/// </summary>
		///
		/// <typeparam name="typename TMultivector">	Type of the typename t float. </typeparam>
		/// <typeparam name="typename FuncOp">			Type of the size_t t u vector space dimension. </typeparam>
		/// <param name="matA">		   	[in,out] The mat a. </param>
		/// <param name="wA">		   	The mv a. </param>
		/// <param name="xMaskB">	   	The mv x coordinate. </param>
		/// <param name="xMaskC">	   	the left. </param>
		/// <param name="bLeftToRight">	true to left to right. </param>
		/// <param name="xFuncOp">	   	The function operation. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TSubspaceBasis, typename TMultivectorX, typename FuncOp>
		void _EvalProductMatrix(CMatrix<typename TSubspaceBasis::TValue>& matA,
				const TMultivectorX& wA,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskB,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskC,
				const TSubspaceBasis& xAlgebraBasis,
				FuncOp xFuncOp)
		{
			typedef typename TSubspaceBasis::TValue TValue;
			typedef typename TSubspaceBasis::TMultivector TMultivector;
			try
			{
				// Create geometric product matrix reduced to subspaces of xMaskB and xMaskC

				size_t uDimB = xMaskB.Count();
				size_t uDimC = xMaskC.Count();

				matA.SetSize(uDimC, uDimB);
				matA.Zero();

				xMaskB.ForEachBasisBladePair(xAlgebraBasis, [&](size_t uIdxB, const TMultivector& wBladeB, const TMultivector& wRecipBladeB)
						{
							_EvalProductMatrix_InnerLoop(matA, wA, uIdxB, wBladeB, xMaskC, xAlgebraBasis, xFuncOp);
						});
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error evaluating product matrix", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Eval product matrix.
		/// </summary>
		///
		/// <exception cref="std::exception">	Thrown when a C  error condition occurs. </exception>
		///
		/// <typeparam name="typename TMultivector">	Type of the typename t multivector. </typeparam>
		/// <typeparam name="typename FuncOp">			Type of the typename function operation. </typeparam>
		/// <param name="matA">		   	[in,out] The mat a. </param>
		/// <param name="wListA">	   	The mv list a. </param>
		/// <param name="xMaskB">	   	The mask b. </param>
		/// <param name="xMaskC">	   	The mask c. </param>
		/// <param name="bLeftToRight">	true to left to right. </param>
		/// <param name="xFuncOp">	   	The function operation. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TSubspaceBasis, typename TMultivectorX, typename FuncOp>
		void _EvalProductMatrix(CMatrix<typename TSubspaceBasis::TValue>& matA,
				const std::vector<TMultivectorX>& wListA,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskB,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskC,
				const TSubspaceBasis& xAlgebraBasis,
				FuncOp xFuncOp)
		{
			typedef typename TSubspaceBasis::TValue TValue;
			typedef typename TSubspaceBasis::TMultivector TMultivector;

			try
			{
				// Create geometric product matrix reduced to subspaces of xMaskB and xMaskC

				const size_t uMvCnt = (size_t) wListA.size();
				const size_t uDimB  = (size_t) xMaskB.Count();
				const size_t uDimC  = (size_t) xMaskC.Count();

				if (uMvCnt == 0)
				{
					TAN_THROW_RT("List of multivectors is empty");
				}

				matA.SetSize(uMvCnt * uDimC, uDimB);
				matA.Zero();

				xMaskB.ForEachBasisBladePair(xAlgebraBasis, [&](size_t uIdxB, const TMultivector& wBladeB, const TMultivector& wRecipBladeB)
						{
							_EvalProductMatrix_InnerLoop(matA, wListA, uIdxB, wBladeB, xMaskC, xAlgebraBasis, xFuncOp);
						});
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error evaluating product matrix", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Eval product matrix.
		/// </summary>
		///
		/// <typeparam name="typename TSubspaceBasis">		 	Type of the typename t basis. </typeparam>
		/// <typeparam name="typename TMultivectorX">	Type of the typename t multivector x coordinate. </typeparam>
		/// <typeparam name="typename FuncOp">		 	Type of the typename function operation. </typeparam>
		/// <param name="matA">				[in,out] The mat a. </param>
		/// <param name="matA">				The mat a. </param>
		/// <param name="xMaskA">			The mask a. </param>
		/// <param name="xMaskB">			The mask b. </param>
		/// <param name="xMaskC">			The mask c. </param>
		/// <param name="xAlgebraBasis">	The algebra basis. </param>
		/// <param name="xFuncOp">			The function operation. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TSubspaceBasis, typename TStyle, typename FuncOp>
		void _EvalProductMatrix(CMatrix<typename TSubspaceBasis::TValue>& matProduct,
				const CMatrix<typename TSubspaceBasis::TValue>& matA,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskA,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskB,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskC,
				const TStyle& xAlgebraBasis,
				FuncOp xFuncOp)
		{
			typedef typename TSubspaceBasis::TValue TValue;
			typedef typename TSubspaceBasis::TMultivector TMultivector;

			// Create geometric product matrix reduced to subspaces of xMaskB and xMaskC

			const size_t uMvCnt = matA.GetColCount();
			const size_t uDimB  = xMaskB.Count();
			const size_t uDimC  = xMaskC.Count();

			try
			{
				if (uMvCnt == 0)
				{
					TAN_THROW_RT("List of multivectors is empty");
				}

				if (matA.GetRowCount() != xMaskA.Count())
				{
					TAN_THROW_RT("Row dimension of input matrix does not agree with mask");
				}

				matProduct.SetSize(uMvCnt * uDimC, uDimB);
				matProduct.Zero();

				xMaskB.ForEachBasisBladePair(xAlgebraBasis, [&](size_t uIdxB, const TMultivector& wBladeB, const TMultivector& wRecipBladeB)
						{
							_EvalProductMatrix_InnerLoop(matProduct, matA, xMaskA, uIdxB, wBladeB, xMaskC, xAlgebraBasis, xFuncOp);
						});
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error evaluating product matrix", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Eval product matrix inner loop.
		/// </summary>
		///
		/// <typeparam name="typename TValue">	Type of the typename t value. </typeparam>
		/// <typeparam name="typename TBlade">	Type of the typename t blade. </typeparam>
		/// <typeparam name="typename FuncOp">	Type of the typename function operation. </typeparam>
		/// <typeparam name="typename FuncOp">	Type of the typename function operation. </typeparam>
		/// <param name="matA">		   	[in,out] The mat a. </param>
		/// <param name="fValA">	   	The value a. </param>
		/// <param name="blA">		   	The bl a. </param>
		/// <param name="xMaskB">	   	The mask b. </param>
		/// <param name="xMaskC">	   	The mask c. </param>
		/// <param name="bLeftToRight">	true to left to right. </param>
		/// <param name="xFuncOp">	   	The function operation. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TSubspaceBasis, typename TMultivectorX, typename FuncOp>
		void _EvalProductMatrix_InnerLoop(CMatrix<typename TSubspaceBasis::TValue>& matA,
				const TMultivectorX& wA,
				size_t uIdxB,
				const typename TSubspaceBasis::TMultivector& wBladeB,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskC,
				const TSubspaceBasis& xAlgebraBasis,
				FuncOp xFuncOp)
		{
			typedef typename TSubspaceBasis::TValue TValue;
			typedef typename TSubspaceBasis::TMultivector TMultivector;

			TValue fValue;
			TMultivector wC;

			xFuncOp(wC, wA, wBladeB);

			xMaskC.ForEachBasisBladePair(xAlgebraBasis, [&](size_t uIdxC, const TMultivector& wBladeC, const TMultivector& wRecipBladeC)
					{
						GA::SP(fValue, wC, wRecipBladeC);
						matA(uIdxC, uIdxB) = fValue;
					});
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Eval product matrix inner loop.
		/// </summary>
		///
		/// <exception cref="std::exception">	Thrown when a C  error condition occurs. </exception>
		///
		/// <typeparam name="typename TValue">	Type of the typename t value. </typeparam>
		/// <typeparam name="typename TBlade">	Type of the typename t blade. </typeparam>
		/// <typeparam name="typename FuncOp">	Type of the typename function operation. </typeparam>
		/// <param name="matA">		   	[in,out] The mat a. </param>
		/// <param name="wListA">	   	The mv list a. </param>
		/// <param name="uIndexB">	   	The index b. </param>
		/// <param name="blB">		   	The bl b. </param>
		/// <param name="xMaskC">	   	The mask c. </param>
		/// <param name="bLeftToRight">	true to left to right. </param>
		/// <param name="xFuncOp">	   	The function operation. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TSubspaceBasis, typename TMultivectorX, typename FuncOp>
		void _EvalProductMatrix_InnerLoop(CMatrix<typename TSubspaceBasis::TValue>& matA,
				const std::vector<TMultivectorX>& vecwListA,
				size_t uIdxB,
				const typename TSubspaceBasis::TMultivector& wBladeB,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskC,
				const TSubspaceBasis& xAlgebraBasis,
				FuncOp xFuncOp)
		{
			typedef typename TSubspaceBasis::TValue TValue;
			typedef typename TSubspaceBasis::TMultivector TMultivector;

			TValue fValue;
			TMultivector wC;
			const size_t uDimC = xMaskC.Count();

			ForEachIndex(vecwListA, [&](const TMultivectorX& wA, size_t uMvIdx)
					{
						const size_t uRowOffset = uMvIdx * uDimC;
						xFuncOp(wC, wA, wBladeB);

						xMaskC.ForEachBasisBladePair(xAlgebraBasis, [&](size_t uIdxC, const TMultivector& wBladeC, const TMultivector& wRecipBladeC)
								{
									GA::SP(fValue, wC, wRecipBladeC);
									matA(uRowOffset + uIdxC, uIdxB) = fValue;
								});
					});
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Eval product matrix inner loop.
		/// </summary>
		///
		/// <typeparam name="typename TSubspaceBasis">		 	Type of the typename t basis. </typeparam>
		/// <typeparam name="typename TMultivectorX">	Type of the typename t multivector x coordinate. </typeparam>
		/// <typeparam name="typename FuncOp">		 	Type of the typename function operation. </typeparam>
		/// <param name="matProduct">   	[in,out] The mat product. </param>
		/// <param name="wListA">			The list a. </param>
		/// <param name="uIdxB">			The index b. </param>
		/// <param name="wBladeB">			The blade b. </param>
		/// <param name="xMaskC">			The mask c. </param>
		/// <param name="xAlgebraBasis">	The algebra basis. </param>
		/// <param name="xFuncOp">			The function operation. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TSubspaceBasis, typename TStyle, typename FuncOp>
		void _EvalProductMatrix_InnerLoop(CMatrix<typename TSubspaceBasis::TValue>& matProduct,
				const CMatrix<typename TSubspaceBasis::TValue>& matA,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskA,
				size_t uIdxB,
				const typename TSubspaceBasis::TMultivector& wBladeB,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskC,
				const TStyle& xAlgebraBasis,
				FuncOp xFuncOp)
		{
			typedef typename TSubspaceBasis::TValue TValue;
			typedef typename TSubspaceBasis::TMultivector TMultivector;

			TValue fValue;
			TMultivector wC;
			TValue* pMatProd;
			const TValue* pMatA;
			const size_t uDimC = xMaskC.Count();

			// Column count of matrix A is the number of multivectors in matrix
			const size_t uMvCnt = matA.GetColCount();

			const size_t uProductMatStep = uDimC * matProduct.GetColCount();

			xMaskA.ForEachBasisBladePair(xAlgebraBasis, [&](size_t uIdxA, const TMultivector& wBladeA, const TMultivector& wRecipBladeA)
					{
						xFuncOp(wC, wBladeA, wBladeB);

						//printf("b(%d), a(%d), wC = wA * wB: %s = %s * %s\n", uIdxB, uIdxA,
						//	xAlgebraBasis.ToString(wC).c_str(), xAlgebraBasis.ToString(wBladeA).c_str(), xAlgebraBasis.ToString(wBladeB).c_str());

						if (!GA::IsZero(wC))
						{
							xMaskC.ForEachBasisBladePair(xAlgebraBasis, [&](size_t uIdxC, const TMultivector& wBladeC, const TMultivector& wRecipBladeC)
									{
										GA::SP(fValue, wC, wRecipBladeC);
										//printf("    c(%d), fValue = wC . wRC: %4.2f = %s . %s\n", uIdxC, fValue,
										//	xAlgebraBasis.ToString(wC).c_str(), xAlgebraBasis.ToString(wRecipBladeC).c_str());

										if (!xAlgebraBasis.IsZero(fValue))
										{
											pMatProd = &(matProduct(uIdxC, uIdxB));
											pMatA = &(matA(uIdxA, 0));

											// Now loop over all multivectors in matA
											for (size_t uMvIdx = 0; uMvIdx < uMvCnt; ++uMvIdx, pMatProd += uProductMatStep, ++pMatA)
											{
												//matProduct(uRowOffset + uIdxC, uIdxB) = fValue * matA(uIdxA, uMvIdx);
												*pMatProd += fValue * (*pMatA);
											}
										}
									});
						}
					});
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Eval product matrix gp.
		/// </summary>
		///
		/// <typeparam name="typename TMultivector">	Type of the typename t multivector. </typeparam>
		/// <typeparam name="typename FuncOp">			Type of the typename function operation. </typeparam>
		/// <param name="matA">		   	[in,out] The mat a. </param>
		/// <param name="wA">		   	The mv a. </param>
		/// <param name="xMaskB">	   	The mask b. </param>
		/// <param name="xMaskC">	   	The mask c. </param>
		/// <param name="bLeftToRight">	(optional) the left to right. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TSubspaceBasis, typename TMultivectorX>
		void EvalProductMatrix_GP_Reverse(CMatrix<typename TSubspaceBasis::TValue>& matA,
				const TMultivectorX& wA,
				const bool bReverseA,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskB,
				const bool bReverseB,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskC,
				const TSubspaceBasis& xAlgebraBasis)
		{
			typedef typename TSubspaceBasis::TValue TValue;
			typedef typename TSubspaceBasis::TMultivector TMultivector;
			try
			{
				_EvalProductMatrix(matA, wA, xMaskB, xMaskC, xAlgebraBasis,
						[&](TMultivector& wC, const TMultivector& wA, const TMultivector& wB)
						{
							GA::GP_Reverse(wC, wA, bReverseA, wB, bReverseB);
						});
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error evaluating product matrix from reverse geometric product", xEx);
			}
		}

		template<typename TSubspaceBasis, typename TMultivectorX>
		void EvalProductMatrix_GP_Reverse(CMatrix<typename TSubspaceBasis::TValue>& matA,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskA,
				const bool bReverseA,
				const TMultivectorX& wB,
				const bool bReverseB,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskC,
				const TSubspaceBasis& xAlgebraBasis)
		{
			typedef typename TSubspaceBasis::TValue TValue;
			typedef typename TSubspaceBasis::TMultivector TMultivector;
			try
			{
				_EvalProductMatrix(matA, wB, xMaskA, xMaskC, xAlgebraBasis,
						[&](TMultivector& wC, const TMultivector& wB, const TMultivector& wA)
						{
							GA::GP_Reverse(wC, wA, bReverseA, wB, bReverseB);
						});
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error evaluating product matrix from reverse geometric product", xEx);
			}
		}

		template<typename TSubspaceBasis, typename TMultivectorX>
		void EvalProductMatrix_GP_Reverse(CMatrix<typename TSubspaceBasis::TValue>& matA,
				const std::vector<TMultivectorX>& wListA,
				const bool bReverseA,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskB,
				const bool bReverseB,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskC,
				const TSubspaceBasis& xAlgebraBasis)
		{
			typedef typename TSubspaceBasis::TValue TValue;
			typedef typename TSubspaceBasis::TMultivector TMultivector;
			try
			{
				_EvalProductMatrix(matA, wListA, xMaskB, xMaskC, xAlgebraBasis,
						[&](TMultivector& wC, const TMultivector& wA, const TMultivector& wB)
						{
							GA::GP_Reverse(wC, wA, bReverseA, wB, bReverseB);
						});
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error evaluating product matrix from reverse geometric product", xEx);
			}
		}

		template<typename TSubspaceBasis, typename TMultivectorX>
		void EvalProductMatrix_GP_Reverse(CMatrix<typename TSubspaceBasis::TValue>& matA,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskA,
				const bool bReverseA,
				const std::vector<TMultivectorX>& wListB,
				const bool bReverseB,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskC,
				const TSubspaceBasis& xAlgebraBasis)
		{
			typedef typename TSubspaceBasis::TValue TValue;
			typedef typename TSubspaceBasis::TMultivector TMultivector;

			try
			{
				_EvalProductMatrix(matA, wListB, xMaskA, xMaskC, xAlgebraBasis,
						[&](TMultivector& wC, const TMultivector& wB, const TMultivector& wA)
						{
							GA::GP_Reverse(wC, wA, bReverseA, wB, bReverseB);
						});
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error evaluating product matrix from reverse geometric product", xEx);
			}
		}

		template<typename TSubspaceBasis, typename TStyle>
		void EvalProductMatrix_GP_Reverse(CMatrix<typename TSubspaceBasis::TValue>& matProduct,
				const CMatrix<typename TSubspaceBasis::TValue>& matA,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskA,
				const bool bReverseA,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskB,
				const bool bReverseB,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskC,
				const TStyle& xAlgebraBasis)
		{
			typedef typename TSubspaceBasis::TValue TValue;
			typedef typename TSubspaceBasis::TMultivector TMultivector;
			try
			{
				_EvalProductMatrix(matProduct, matA, xMaskA, xMaskB, xMaskC, xAlgebraBasis,
						[&](TMultivector& wC, const TMultivector& wA, const TMultivector& wB)
						{
							GA::GP_Reverse(wC, wA, bReverseA, wB, bReverseB);
						});
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error evaluating product matrix from reverse geometric product", xEx);
			}
		}

		template<typename TSubspaceBasis, typename TStyle>
		void EvalProductMatrix_GP_Reverse(CMatrix<typename TSubspaceBasis::TValue>& matProduct,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskA,
				const bool bReverseA,
				const CMatrix<typename TSubspaceBasis::TValue>& matB,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskB,
				const bool bReverseB,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskC,
				const TStyle& xAlgebraBasis)
		{
			typedef typename TSubspaceBasis::TValue TValue;
			typedef typename TSubspaceBasis::TMultivector TMultivector;

			try
			{
				_EvalProductMatrix(matProduct, matB, xMaskB, xMaskA, xMaskC, xAlgebraBasis,
						[&](TMultivector& wC, const TMultivector& wB, const TMultivector& wA)
						{
							GA::GP_Reverse(wC, wA, bReverseA, wB, bReverseB);
						});
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error evaluating product matrix from reverse geometric product", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Eval product matrix operation reverse.
		/// </summary>
		///
		/// <typeparam name="TSubspaceBasis">	Type of the subspace basis. </typeparam>
		/// <typeparam name="TMultivectorX"> 	Type of the multivector x coordinate. </typeparam>
		/// <param name="matA">				[in,out] The mat a. </param>
		/// <param name="wA">				The w a. </param>
		/// <param name="bReverseA">		The reverse a. </param>
		/// <param name="xMaskB">			The mask b. </param>
		/// <param name="bReverseB">		The reverse b. </param>
		/// <param name="xMaskC">			The mask c. </param>
		/// <param name="xAlgebraBasis">	The algebra basis. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TSubspaceBasis, typename TMultivectorX>
		void EvalProductMatrix_OP_Reverse(CMatrix<typename TSubspaceBasis::TValue>& matA,
				const TMultivectorX& wA,
				const bool bReverseA,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskB,
				const bool bReverseB,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskC,
				const TSubspaceBasis& xAlgebraBasis)
		{
			typedef typename TSubspaceBasis::TValue TValue;
			typedef typename TSubspaceBasis::TMultivector TMultivector;
			try
			{
				_EvalProductMatrix(matA, wA, xMaskB, xMaskC, xAlgebraBasis,
						[&](TMultivector& wC, const TMultivector& wA, const TMultivector& wB)
						{
							GA::OP_Reverse(wC, wA, bReverseA, wB, bReverseB);
						});
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error evaluating product matrix from reverse geometric product", xEx);
			}
		}

		template<typename TSubspaceBasis, typename TMultivectorX>
		void EvalProductMatrix_OP_Reverse(CMatrix<typename TSubspaceBasis::TValue>& matA,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskA,
				const bool bReverseA,
				const TMultivectorX& wB,
				const bool bReverseB,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskC,
				const TSubspaceBasis& xAlgebraBasis)
		{
			typedef typename TSubspaceBasis::TValue TValue;
			typedef typename TSubspaceBasis::TMultivector TMultivector;
			try
			{
				_EvalProductMatrix(matA, wB, xMaskA, xMaskC, xAlgebraBasis,
						[&](TMultivector& wC, const TMultivector& wB, const TMultivector& wA)
						{
							GA::OP_Reverse(wC, wA, bReverseA, wB, bReverseB);
						});
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error evaluating product matrix from reverse geometric product", xEx);
			}
		}

		template<typename TSubspaceBasis, typename TMultivectorX>
		void EvalProductMatrix_OP_Reverse(CMatrix<typename TSubspaceBasis::TValue>& matA,
				const std::vector<TMultivectorX>& wListA,
				const bool bReverseA,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskB,
				const bool bReverseB,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskC,
				const TSubspaceBasis& xAlgebraBasis)
		{
			typedef typename TSubspaceBasis::TValue TValue;
			typedef typename TSubspaceBasis::TMultivector TMultivector;
			try
			{
				_EvalProductMatrix(matA, wListA, xMaskB, xMaskC, xAlgebraBasis,
						[&](TMultivector& wC, const TMultivector& wA, const TMultivector& wB)
						{
							GA::OP_Reverse(wC, wA, bReverseA, wB, bReverseB);
						});
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error evaluating product matrix from reverse geometric product", xEx);
			}
		}

		template<typename TSubspaceBasis, typename TMultivectorX>
		void EvalProductMatrix_OP_Reverse(CMatrix<typename TSubspaceBasis::TValue>& matA,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskA,
				const bool bReverseA,
				const std::vector<TMultivectorX>& wListB,
				const bool bReverseB,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskC,
				const TSubspaceBasis& xAlgebraBasis)
		{
			typedef typename TSubspaceBasis::TValue TValue;
			typedef typename TSubspaceBasis::TMultivector TMultivector;

			try
			{
				_EvalProductMatrix(matA, wListB, xMaskA, xMaskC, xAlgebraBasis,
						[&](TMultivector& wC, const TMultivector& wB, const TMultivector& wA)
						{
							GA::OP_Reverse(wC, wA, bReverseA, wB, bReverseB);
						});
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error evaluating product matrix from reverse geometric product", xEx);
			}
		}

		template<typename TSubspaceBasis, typename TStyle>
		void EvalProductMatrix_OP_Reverse(CMatrix<typename TSubspaceBasis::TValue>& matProduct,
				const CMatrix<typename TSubspaceBasis::TValue>& matA,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskA,
				const bool bReverseA,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskB,
				const bool bReverseB,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskC,
				const TStyle& xAlgebraBasis)
		{
			typedef typename TSubspaceBasis::TValue TValue;
			typedef typename TSubspaceBasis::TMultivector TMultivector;
			try
			{
				_EvalProductMatrix(matProduct, matA, xMaskA, xMaskB, xMaskC, xAlgebraBasis,
						[&](TMultivector& wC, const TMultivector& wA, const TMultivector& wB)
						{
							GA::OP_Reverse(wC, wA, bReverseA, wB, bReverseB);
						});
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error evaluating product matrix from reverse geometric product", xEx);
			}
		}

		template<typename TSubspaceBasis, typename TStyle>
		void EvalProductMatrix_OP_Reverse(CMatrix<typename TSubspaceBasis::TValue>& matProduct,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskA,
				const bool bReverseA,
				const CMatrix<typename TSubspaceBasis::TValue>& matB,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskB,
				const bool bReverseB,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskC,
				const TStyle& xAlgebraBasis)
		{
			typedef typename TSubspaceBasis::TValue TValue;
			typedef typename TSubspaceBasis::TMultivector TMultivector;

			try
			{
				_EvalProductMatrix(matProduct, matB, xMaskB, xMaskA, xMaskC, xAlgebraBasis,
						[&](TMultivector& wC, const TMultivector& wB, const TMultivector& wA)
						{
							GA::OP_Reverse(wC, wA, bReverseA, wB, bReverseB);
						});
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error evaluating product matrix from reverse geometric product", xEx);
			}
		}

		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		/// <summary>
		/// 	Eval product matrix IP reverse.
		/// </summary>
		///
		/// <typeparam name="TSubspaceBasis">	Type of the subspace basis. </typeparam>
		/// <typeparam name="TMultivectorX"> 	Type of the multivector x coordinate. </typeparam>
		/// <param name="matA">				[in,out] The mat a. </param>
		/// <param name="wA">				The w a. </param>
		/// <param name="bReverseA">		The reverse a. </param>
		/// <param name="xMaskB">			The mask b. </param>
		/// <param name="bReverseB">		The reverse b. </param>
		/// <param name="xMaskC">			The mask c. </param>
		/// <param name="xAlgebraBasis">	The algebra basis. </param>
		/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
		template<typename TSubspaceBasis, typename TMultivectorX>
		void EvalProductMatrix_IP_Reverse(CMatrix<typename TSubspaceBasis::TValue>& matA,
				const TMultivectorX& wA,
				const bool bReverseA,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskB,
				const bool bReverseB,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskC,
				const TSubspaceBasis& xAlgebraBasis)
		{
			typedef typename TSubspaceBasis::TValue TValue;
			typedef typename TSubspaceBasis::TMultivector TMultivector;
			try
			{
				_EvalProductMatrix(matA, wA, xMaskB, xMaskC, xAlgebraBasis,
						[&](TMultivector& wC, const TMultivector& wA, const TMultivector& wB)
						{
							GA::IP_Reverse(wC, wA, bReverseA, wB, bReverseB);
						});
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error evaluating product matrix from reverse geometric product", xEx);
			}
		}

		template<typename TSubspaceBasis, typename TMultivectorX>
		void EvalProductMatrix_IP_Reverse(CMatrix<typename TSubspaceBasis::TValue>& matA,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskA,
				const bool bReverseA,
				const TMultivectorX& wB,
				const bool bReverseB,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskC,
				const TSubspaceBasis& xAlgebraBasis)
		{
			typedef typename TSubspaceBasis::TValue TValue;
			typedef typename TSubspaceBasis::TMultivector TMultivector;
			try
			{
				_EvalProductMatrix(matA, wB, xMaskA, xMaskC, xAlgebraBasis,
						[&](TMultivector& wC, const TMultivector& wB, const TMultivector& wA)
						{
							GA::IP_Reverse(wC, wA, bReverseA, wB, bReverseB);
						});
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error evaluating product matrix from reverse geometric product", xEx);
			}
		}

		template<typename TSubspaceBasis, typename TMultivectorX>
		void EvalProductMatrix_IP_Reverse(CMatrix<typename TSubspaceBasis::TValue>& matA,
				const std::vector<TMultivectorX>& wListA,
				const bool bReverseA,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskB,
				const bool bReverseB,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskC,
				const TSubspaceBasis& xAlgebraBasis)
		{
			typedef typename TSubspaceBasis::TValue TValue;
			typedef typename TSubspaceBasis::TMultivector TMultivector;
			try
			{
				_EvalProductMatrix(matA, wListA, xMaskB, xMaskC, xAlgebraBasis,
						[&](TMultivector& wC, const TMultivector& wA, const TMultivector& wB)
						{
							GA::IP_Reverse(wC, wA, bReverseA, wB, bReverseB);
						});
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error evaluating product matrix from reverse geometric product", xEx);
			}
		}

		template<typename TSubspaceBasis, typename TMultivectorX>
		void EvalProductMatrix_IP_Reverse(CMatrix<typename TSubspaceBasis::TValue>& matA,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskA,
				const bool bReverseA,
				const std::vector<TMultivectorX>& wListB,
				const bool bReverseB,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskC,
				const TSubspaceBasis& xAlgebraBasis)
		{
			typedef typename TSubspaceBasis::TValue TValue;
			typedef typename TSubspaceBasis::TMultivector TMultivector;

			try
			{
				_EvalProductMatrix(matA, wListB, xMaskA, xMaskC, xAlgebraBasis,
						[&](TMultivector& wC, const TMultivector& wB, const TMultivector& wA)
						{
							GA::IP_Reverse(wC, wA, bReverseA, wB, bReverseB);
						});
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error evaluating product matrix from reverse geometric product", xEx);
			}
		}

		template<typename TSubspaceBasis, typename TStyle>
		void EvalProductMatrix_IP_Reverse(CMatrix<typename TSubspaceBasis::TValue>& matProduct,
				const CMatrix<typename TSubspaceBasis::TValue>& matA,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskA,
				const bool bReverseA,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskB,
				const bool bReverseB,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskC,
				const TStyle& xAlgebraBasis)
		{
			typedef typename TSubspaceBasis::TValue TValue;
			typedef typename TSubspaceBasis::TMultivector TMultivector;
			try
			{
				_EvalProductMatrix(matProduct, matA, xMaskA, xMaskB, xMaskC, xAlgebraBasis,
						[&](TMultivector& wC, const TMultivector& wA, const TMultivector& wB)
						{
							GA::IP_Reverse(wC, wA, bReverseA, wB, bReverseB);
						});
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error evaluating product matrix from reverse geometric product", xEx);
			}
		}

		template<typename TSubspaceBasis, typename TStyle>
		void EvalProductMatrix_IP_Reverse(CMatrix<typename TSubspaceBasis::TValue>& matProduct,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskA,
				const bool bReverseA,
				const CMatrix<typename TSubspaceBasis::TValue>& matB,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskB,
				const bool bReverseB,
				const GA::CSubspaceMask<TSubspaceBasis>& xMaskC,
				const TStyle& xAlgebraBasis)
		{
			typedef typename TSubspaceBasis::TValue TValue;
			typedef typename TSubspaceBasis::TMultivector TMultivector;

			try
			{
				_EvalProductMatrix(matProduct, matB, xMaskB, xMaskA, xMaskC, xAlgebraBasis,
						[&](TMultivector& wC, const TMultivector& wB, const TMultivector& wA)
						{
							GA::IP_Reverse(wC, wA, bReverseA, wB, bReverseB);
						});
			}
			catch (std::exception& xEx)
			{
				TAN_RETHROW("Error evaluating product matrix from reverse geometric product", xEx);
			}
		}
	}
}	// .GA
