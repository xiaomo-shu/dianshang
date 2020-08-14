#ifndef __V_YZY_PROTOCOL_H__
#define __V_YZY_PROTOCOL_H__

typedef unsigned char  u8_t;
typedef unsigned short u16_t;
typedef unsigned int   u32_t;

#ifndef NULL
#define NULL            ((void *) 0)
#endif

#define MAJOR_VER       1
#define MINOR_VER       0   

typedef enum vYzyProtocolStatus {
    E_YZY_PROTOCOL_SUCCESS   = 0,       //操作成功
    E_YZY_PROTOCOL_PARAMETER_ERR,       //参数错误
    E_YZY_PROTOCOL_INSUFFICIENT_SPACE,  //内存空间不足
    E_YZY_PROTOCOL_PROTOCOL_ERR,        //协议错误
} eYzyProtocolStatus;

typedef enum vYzySrvCode {
    E_SC_KEEP_ONLINE = 0,
} vYzySrvCode;


#define Big_str2u16(s)       ( (((u16_t)(s)[0])<<8) + ((u16_t)(s)[1]) )
#define Big_str2u32(s)       ( (((u32_t)(s)[0])<<24) + (((u32_t)(s)[1])<<16) + \
                               (((u32_t)(s)[2])<<8) + ((u32_t)(s)[3]) )
#define Big_u16ToStr(s, n)    do{  (s)[1] = (u8_t)((n)&0xFF);  (s)[0] = (u8_t)(((n)>>8)&0xFF);  }while(0)
#define Big_u32ToStr(s, n)    do{  (s)[3] = (u8_t)((n)&0xFF);        (s)[2] = (u8_t)(((n)>>8)&0xFF); \
                                   (s)[1] = (u8_t)(((n)>>16)&0xFF);  (s)[0] = (u8_t)(((n)>>24)&0xFF);    }while(0)

#define Little_str2u16(s)      ( (((u16_t)(s)[1])<<8) + ((u16_t)(s)[0]) )
#define Little_str2u32(s)      ( (((u32_t)(s)[3])<<24) + (((u32_t)(s)[2])<<16) + \
                                 (((u32_t)(s)[1])<<8) + ((u32_t)(s)[0]) )
#define Little_u16ToStr(s, n)  do{  (s)[0] = (u8_t)((n)&0xFF);  (s)[1] = (u8_t)(((n)>>8)&0xFF);  }while(0)
#define Little_u32ToStr(s, n)  do{  (s)[0] = (u8_t)((n)&0xFF);        (s)[1] = (u8_t)(((n)>>8)&0xFF); \
                                    (s)[2] = (u8_t)(((n)>>16)&0xFF);  (s)[3] = (u8_t)(((n)>>24)&0xFF);    }while(0)                               

//大端序则为 1，小端序为 0
#if 1
    //
    #define STR_TO_U16(s)    Big_str2u16(s)
    #define STR_TO_U32(s)    Big_str2u32(s)
    #define U16_TO_STR(s, n) Big_u16ToStr(s, n)
    #define U32_TO_STR(s, n) Big_u32ToStr(s, n)
#else
    #define STR_TO_U16(s)    Little_str2u16(s)
    #define STR_TO_U32(s)    Little_str2u32(s)
    #define U16_TO_STR(s, n) Little_u16ToStr(s, n)
    #define U32_TO_STR(s, n) Little_u32ToStr(s, n)
#endif

// 2字节对齐 // request headr size 26
//#pragma pack(2)
#pragma pack(push, 1)

typedef struct vYzyProtocolRequest vYzyProtocolRequest;
struct vYzyProtocolRequest {
    u16_t  version_chief;       //主版本号       例如  0x0001
    u16_t  version_sub;         //次要版本号     例如  0x0001
    u32_t  service_code;        //请求的服务编号  例如 0xff00ff01
    u32_t  request_code;        //请求编号       例如 0x00000001  用于区别每个链接每次请求的唯一性
    u32_t  dataSize;            //数据域大小     例如 0x00001000
    u8_t   dataType;            //数据段类型      例如 0x00:二进制数据 0x01:json 0x02:protobuf
    u8_t   encoding;            //数据段压缩方式  例如 0x00:无压缩
    u16_t  tokenLength;         //token长度     没有就是 0x0000
    u16_t  supplementary;       //补充协议头长度  没有就是 0x0000
    // u8_t   supplementarys[0];   //补充协议头数据段
    // u8_t   token[0];            //token数据段
    u8_t   data[0];             //数据段
};

// Response headr size 18
typedef struct vYzyProtocolResponse vYzyProtocolResponse;
struct vYzyProtocolResponse {
    u16_t  version_chief;       //主版本号      例如  0x0001
    u16_t  version_sub;         //次要版本号    例如  0x0001
    u32_t  service_code;        //响应服务编号   例如 0xff00ff01
    u32_t  response_code;       //响应编号      例如 0x00000001  用于对应请求
    u32_t  dataSize;            //数据域大小     例如 0x00001000
    u8_t   dataType;            //数据段类型     例如 0x00:二进制数据 0x01:json 0x02:protobuf
    u8_t   encoding;            //数据段压缩方式  例如 0x00:无压缩
    u8_t   data[0];             //数据段
};

#pragma pack(pop)

/**************************************************************
* 名称 : u32YzyProtocol_RequestCreate
* 功能 : 创建协议请求包
* 参数 : srv_code : in : 请求的服务编号
         dataSize : in : 数据段长度
         dataType : in : 数据段类型      例如 0x00:二进制数据 0x01:json 0x02:protobuf
         encoding : in : 数据段压缩方式  例如 0x00:无压缩
         pu8Payload : in : 数据负载
         pu32PktSize : out : 创建的协议包长度
         ppvPktData : out : 创建的协议包数据
* 返回 : 创建结果，查看 eYzyProtocolStatus 枚举体成员
* 备注 : 1. 创建的请求包数据内存需要调用销毁函数销毁
**************************************************************/
u32_t u32YzyProtocol_RequestCreate(u32_t srv_code, \
                                   u32_t dataSize, u8_t dataType, u8_t encoding, u8_t *pu8Payload, \
                                   u16_t tokenLen, u8_t *pToken, \
                                   u32_t *pu32PktSize, void **ppvPktData);

/**************************************************************
* 名称 : u32YzyProtocol_ResponseCreate
* 功能 : 创建协议响应包
* 参数 : srv_code : in : 请求的服务编号
         rsp_code : in : 响应编号，及请求编号
         dataSize : in : 数据段长度
         dataType : in : 数据段类型      例如 0x00:二进制数据 0x01:json 0x02:protobuf
         encoding : in : 数据段压缩方式  例如 0x00:无压缩
         pu8Payload : in : 数据负载
         pu32PktSize : out : 创建的协议包长度
         ppvPktData : out : 创建的协议包数据
* 返回 : 创建结果，查看 eYzyProtocolStatus 枚举体成员
* 备注 : 1. 创建的协议包数据内存需要调用销毁函数销毁
**************************************************************/
u32_t u32YzyProtocol_ResponseCreate(u32_t srv_code, u32_t rsp_code, \
                                    u32_t dataSize, u8_t dataType, u8_t encoding, u8_t *pu8Payload, \
                                    u32_t *pu32PktSize, void **ppvPktData);

/**************************************************************
* 名称 : u32YzyProtocol_RequestParse
* 功能 : 解析请求包
* 参数 : pu8Data : in : 请求包数据
         u32Size : in : 请求包长度
         ppYzyProtoReq : out : 解析后的协议字段
* 返回 : 解析结果，查看 eYzyProtocolStatus 枚举体成员
* 备注 : 1. 创建的协议包数据内存需要调用销毁函数销毁
**************************************************************/
u32_t u32YzyProtocol_RequestParse(u8_t *pu8Data, u32_t u32Size, vYzyProtocolRequest **ppYzyProtoReq);

/**************************************************************
* 名称 : u32YzyProtocol_ResponseParse
* 功能 : 解析响应包
* 参数 : pu8Data : in : 请求包数据
         u32Size : in : 请求包长度
         ppYzyProtoRsp : out : 解析后的协议字段
* 返回 : 解析结果，查看 eYzyProtocolStatus 枚举体成员
* 备注 : 1. 创建的协议包数据内存需要调用销毁函数销毁
**************************************************************/
u32_t u32YzyProtocol_ResponseParse(u8_t *pu8Data, u32_t u32Size, vYzyProtocolResponse **ppYzyProtoRsp);

/**************************************************************
* 名称 : vYzyProtocol_Destroy
* 功能 : 销毁申请的数据内存
* 参数 : pvPtr : in : 数据指针
* 返回 : 无
* 备注 : 无 
**************************************************************/                    
void vYzyProtocol_Destroy(void *pvPtr);

#endif